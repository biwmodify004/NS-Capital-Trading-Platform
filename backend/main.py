"""NS Capital MT5 gateway. Run only on a trusted Windows host with MetaTrader 5 installed.
No public trading enabled by default. Google ID tokens are verified on each request.
"""
import os
from datetime import datetime, timezone
from threading import Lock
from typing import Literal
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
load_dotenv()
app = FastAPI(title='NS Capital MT5 Gateway', version='0.2.0')
origins = [x.strip() for x in os.getenv('ALLOWED_ORIGINS','http://localhost:5173').split(',') if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=['GET','POST'], allow_headers=['Authorization','Content-Type'])
_lock = Lock()
_killed = True  # fail closed after every server restart

def user(authorization: str = Header(default='')):
    client_id = os.getenv('GOOGLE_CLIENT_ID','')
    if not client_id or not authorization.startswith('Bearer '):
        raise HTTPException(401, 'Google authentication required')
    try:
        claims = id_token.verify_oauth2_token(authorization[7:], google_requests.Request(), client_id)
        if not claims.get('email_verified'):
            raise ValueError('Unverified email')
        allow = [e.strip().lower() for e in os.getenv('ALLOWED_EMAILS','').split(',') if e.strip()]
        if not allow or claims.get('email','').lower() not in allow:
            raise HTTPException(403, 'User not authorized for this trading account')
        return claims
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(401, 'Invalid Google token')

def terminal():
    if os.getenv('MT5_ENABLED','false').lower() != 'true':
        raise HTTPException(503,'MT5 bridge disabled')
    try:
        import MetaTrader5 as mt5
    except ImportError:
        raise HTTPException(503,'MetaTrader5 package requires Windows MT5 terminal')
    path = os.getenv('MT5_TERMINAL_PATH') or None
    kwargs = {'path':path} if path else {}
    login = os.getenv('MT5_LOGIN','')
    if login:
        kwargs.update(login=int(login),password=os.getenv('MT5_PASSWORD',''),server=os.getenv('MT5_SERVER',''))
    if not mt5.initialize(**kwargs):
        raise HTTPException(503,'MT5 connection failed')
    return mt5

@app.get('/api/health')
def health():
    return {'status':'ok','mt5_enabled':os.getenv('MT5_ENABLED','false')=='true','trading_enabled':os.getenv('TRADING_ENABLED','false')=='true','kill_switch':_killed}

@app.get('/api/account')
def account(_=Depends(user)):
    mt5=terminal()
    a=mt5.account_info()
    if a is None: raise HTTPException(503,'MT5 account unavailable')
    return {'login':a.login,'balance':a.balance,'equity':a.equity,'margin':a.margin,'margin_free':a.margin_free,'currency':a.currency,'server':a.server}

@app.get('/api/candles')
def candles(symbol:str='XAUUSD',timeframe:Literal['M1','M5','M15','M30','H1','H4','D1']='M15',count:int=200,_=Depends(user)):
    if count<1 or count>1000: raise HTTPException(422,'count out of range')
    mt5=terminal()
    if not mt5.symbol_select(symbol,True): raise HTTPException(404,'Symbol unavailable')
    tf=getattr(mt5,'TIMEFRAME_'+timeframe)
    rates=mt5.copy_rates_from_pos(symbol,tf,0,count)
    if rates is None: raise HTTPException(503,'MT5 rates unavailable')
    return [{'time':int(r['time']),'open':float(r['open']),'high':float(r['high']),'low':float(r['low']),'close':float(r['close']),'volume':int(r['tick_volume'])} for r in rates]

@app.get('/api/trades')
def trades(_=Depends(user)):
    mt5=terminal()
    from datetime import timedelta
    deals=mt5.history_deals_get(datetime.now(timezone.utc)-timedelta(days=90),datetime.now(timezone.utc))
    if deals is None: raise HTTPException(503,'MT5 trade history unavailable')
    return [{'ticket':d.ticket,'order':d.order,'position_id':d.position_id,'time':d.time,'symbol':d.symbol,'volume':d.volume,'price':d.price,'profit':d.profit,'commission':d.commission,'swap':d.swap,'entry':d.entry} for d in deals]

class Order(BaseModel):
    symbol:str=Field(min_length=1,max_length=32)
    side:Literal['BUY','SELL']
    volume:float=Field(gt=0,le=100)
    sl:float=Field(gt=0)
    tp:float=Field(gt=0)
    confirm_live:bool=False

@app.post('/api/orders/preview')
def preview(order:Order,_=Depends(user)):
    mt5=terminal()
    if not mt5.symbol_select(order.symbol,True): raise HTTPException(404,'Symbol unavailable')
    tick=mt5.symbol_info_tick(order.symbol)
    info=mt5.symbol_info(order.symbol)
    account=mt5.account_info()
    if not tick or not info or not account: raise HTTPException(503,'Quote or account unavailable')
    entry=tick.ask if order.side=='BUY' else tick.bid
    if order.side=='BUY' and not(order.sl<entry<order.tp) or order.side=='SELL' and not(order.tp<entry<order.sl):
        raise HTTPException(422,'SL/TP on wrong side of market')
    if order.volume < info.volume_min or order.volume > info.volume_max or abs(round(order.volume/info.volume_step)*info.volume_step-order.volume)>1e-7:
        raise HTTPException(422,'Invalid volume increment')
    side=mt5.ORDER_TYPE_BUY if order.side=='BUY' else mt5.ORDER_TYPE_SELL
    loss=mt5.order_calc_profit(side,order.symbol,order.volume,entry,order.sl)
    if loss is None or loss>=0: raise HTTPException(422,'Unable to calculate stop loss risk')
    risk_limit=float(os.getenv('MAX_RISK_PERCENT','0.25'))
    risk_pct=abs(loss)/account.equity*100 if account.equity>0 else float('inf')
    return {'entry':entry,'estimated_loss':round(loss,2),'risk_pct':round(risk_pct,4),'max_risk_pct':risk_limit,'approved':risk_pct<=risk_limit,'currency':account.currency}

@app.post('/api/orders')
def place(order:Order,_=Depends(user)):
    with _lock:
        if _killed or os.getenv('TRADING_ENABLED','false').lower()!='true' or not order.confirm_live:
            raise HTTPException(403,'Live trading locked; explicit confirmation required')
        p=preview(order,_)
        if not p['approved']: raise HTTPException(403,'Risk per trade exceeded')
        # Fail closed until daily realized + floating loss, existing exposure,
        # stop levels, market hours and duplicate-order controls are enforced.
        raise HTTPException(501,'Order routing intentionally disabled pending full server-side risk controls')

@app.post('/api/kill-switch')
def kill(_=Depends(user)):
    global _killed
    with _lock: _killed=True
    return {'kill_switch':True,'note':'New orders blocked; existing positions are not automatically closed'}

# V3 signal persistence and protected execution API
from .execution import register
register(app,user,terminal)
