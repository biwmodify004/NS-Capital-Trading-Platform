"""Fail-closed controls. Run execution on a dedicated single-worker Windows bridge."""
import os, math
from datetime import datetime, timezone
from fastapi import HTTPException

def setting(name,default): return float(os.getenv(name,str(default)))
def check_order(mt5, order):
    acc=mt5.account_info(); info=mt5.symbol_info(order.symbol); tick=mt5.symbol_info_tick(order.symbol)
    if not all((acc,info,tick)) or acc.equity<=0: raise HTTPException(503,"Account/quote unavailable")
    if not info.trade_mode or not info.visible: raise HTTPException(403,"Symbol not tradeable")
    if not math.isfinite(order.volume) or order.volume<info.volume_min-1e-8 or order.volume>info.volume_max+1e-8: raise HTTPException(422,"Invalid lot")
    steps=(order.volume-info.volume_min)/info.volume_step
    if abs(steps-round(steps))>1e-5: raise HTTPException(422,"Invalid lot step")
    side=mt5.ORDER_TYPE_BUY if order.side=='BUY' else mt5.ORDER_TYPE_SELL
    entry=tick.ask if order.side=='BUY' else tick.bid
    if not math.isfinite(entry) or entry<=0: raise HTTPException(503,"Bad quote")
    if not ((order.sl<entry<order.tp) if order.side=='BUY' else (order.tp<entry<order.sl)): raise HTTPException(422,"Invalid SL/TP")
    if min(abs(entry-order.sl),abs(entry-order.tp)) < info.trade_stops_level*info.point: raise HTTPException(422,"Broker minimum stop distance")
    loss=mt5.order_calc_profit(side,order.symbol,order.volume,entry,order.sl)
    if loss is None or not math.isfinite(loss) or loss>=0: raise HTTPException(403,"Risk calculation failed")
    risk=abs(loss)/acc.equity*100
    if risk>setting('MAX_RISK_PERCENT',0.25): raise HTTPException(403,"Risk per trade exceeded")
    positions=mt5.positions_get(); pending=mt5.orders_get()
    if positions is None or pending is None: raise HTTPException(503,"Exposure unavailable")
    if len(positions)+len(pending)>=int(os.getenv('MAX_ACTIVE_ORDERS','2')): raise HTTPException(403,"Max open/pending orders")
    if any(p.symbol==order.symbol for p in positions) or any(p.symbol==order.symbol for p in pending): raise HTTPException(403,"Duplicate symbol exposure")
    now=datetime.now(timezone.utc); start=now.replace(hour=0,minute=0,second=0,microsecond=0)
    deals=mt5.history_deals_get(start,now)
    if deals is None: raise HTTPException(503,"Daily history unavailable")
    realized=sum(float(d.profit+d.commission+d.swap) for d in deals)
    floating=sum(float(p.profit+p.swap) for p in positions)
    day_loss=max(0,-realized-floating)
    if day_loss+abs(loss)>acc.balance*setting('DAILY_LOSS_LIMIT_PERCENT',2.0)/100: raise HTTPException(403,"Daily loss budget exceeded")
    if acc.margin_level and acc.margin_level<setting('MIN_MARGIN_LEVEL',200): raise HTTPException(403,"Margin level too low")
    check=mt5.order_check({'action':mt5.TRADE_ACTION_DEAL,'symbol':order.symbol,'volume':order.volume,'type':side,'price':entry,'sl':order.sl,'tp':order.tp,'deviation':int(os.getenv('MAX_DEVIATION_POINTS','20')),'type_time':mt5.ORDER_TIME_GTC,'type_filling':mt5.ORDER_FILLING_IOC})
    if check is None or check.retcode not in (0,mt5.TRADE_RETCODE_DONE): raise HTTPException(403,f"Broker precheck rejected: {getattr(check,'comment','unavailable')}")
    return {'entry':entry,'risk_pct':round(risk,4),'estimated_loss':round(loss,2),'realized_today':round(realized,2),'floating':round(floating,2),'positions':len(positions),'pending':len(pending)}
