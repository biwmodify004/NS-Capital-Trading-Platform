import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from threading import Lock
from .database import SessionLocal, Audit, Signal
from .risk_engine import check_order
router=APIRouter(prefix='/api/v3')
_lock=Lock()
_killed=True
class Order(BaseModel):
    symbol:str=Field(pattern=r'^[A-Za-z0-9._-]{2,32}$')
    side:Literal['BUY','SELL']
    volume:float=Field(gt=0,le=100)
    sl:float=Field(gt=0)
    tp:float=Field(gt=0)
class SignalRequest(Order):
    strategy:str=Field(min_length=2,max_length=100)
    confidence:float=Field(ge=0,le=1)

def register(app,auth,terminal):
    @router.get('/signals')
    def signals(claims=Depends(auth)):
        with SessionLocal() as db:
            rows=db.query(Signal).order_by(Signal.id.desc()).limit(100).all()
            return [{'id':s.id,'strategy':s.strategy,'symbol':s.symbol,'side':s.side,'confidence':s.confidence,'state':s.state,'ticket':s.mt5_ticket} for s in rows]
    @router.post('/signals')
    def propose(payload:SignalRequest,claims=Depends(auth)):
        with SessionLocal() as db:
            s=Signal(**payload.model_dump(),state='PROPOSED');db.add(s);db.add(Audit(actor=claims['email'],action='PROPOSE',details=payload.model_dump_json()));db.commit();db.refresh(s)
            return {'id':s.id,'state':s.state,'note':'Proposal only; execution requires explicit arming'}
    @router.post('/orders/preview')
    def preview(order:Order,claims=Depends(auth)):
        return check_order(terminal(),order)
    @router.post('/kill')
    def kill(claims=Depends(auth)):
        global _killed
        with _lock: _killed=True
        with SessionLocal() as db:
            db.add(Audit(actor=claims['email'],action='KILL',details='New orders blocked'));db.commit()
        return {'kill_switch':True,'note':'Does not close existing positions'}
    @router.get('/status')
    def status(claims=Depends(auth)):
        return {'kill_switch':_killed,'trading_enabled':os.getenv('TRADING_ENABLED','false')=='true','ai_execution_enabled':os.getenv('AI_EXECUTION_ENABLED','false')=='true'}
    @router.post('/signals/{signal_id}/execute')
    def execute(signal_id:int,claims=Depends(auth)):
        global _killed
        with _lock:
            if _killed or os.getenv('TRADING_ENABLED','false')!='true' or os.getenv('AI_EXECUTION_ENABLED','false')!='true': raise HTTPException(403,'Trading locked: default fail closed')
            if os.getenv('EXECUTION_BRIDGE_READY','false')!='true': raise HTTPException(503,'Bridge not commissioned')
            # Intentionally fail closed until a dedicated, tested execution worker with
            # idempotency, atomic state, broker-specific filling and emergency recovery exists.
            raise HTTPException(501,'Execution worker not commissioned; no order submitted')
    app.include_router(router)
