#!/usr/bin/env python3
"""DEXORZO V8 — 60-second MetaQuotes-Demo execution smoke test."""
import time
import MetaTrader5 as mt5
MAGIC=762005
SYMBOL="EURUSD"
VOLUME=0.01
SECONDS=60
def guard():
    a=mt5.account_info(); t=mt5.terminal_info()
    if a is None or t is None: raise RuntimeError("MT5 account/terminal unavailable")
    if "MetaQuotes-Demo" not in str(a.server or ""): raise RuntimeError(f"SAFETY LOCK: Demo only. Current server: {a.server}")
    if not getattr(a,"trade_allowed",False) or not getattr(t,"trade_allowed",False): raise RuntimeError("SAFETY LOCK: MT5 trading permission is disabled")
    return a
def send(req):
    for mode in (mt5.ORDER_FILLING_FOK,mt5.ORDER_FILLING_IOC,mt5.ORDER_FILLING_RETURN):
        r=dict(req); r["type_filling"]=mode
        c=mt5.order_check(r)
        if c is not None and getattr(c,"retcode",None) in (0,mt5.TRADE_RETCODE_DONE):
            x=mt5.order_send(r)
            if x is not None and x.retcode in {mt5.TRADE_RETCODE_DONE,getattr(mt5,"TRADE_RETCODE_DONE_PARTIAL",-1)}: return x
    raise RuntimeError(f"Demo order failed: {mt5.last_error()}")
def main():
    if not mt5.initialize(): raise RuntimeError(mt5.last_error())
    try:
        a=guard()
        print(f"Connected: {a.server} | Login {a.login} | Balance USD {a.balance:,.2f} | Equity USD {a.equity:,.2f}")
        mt5.symbol_select(SYMBOL,True); t=mt5.symbol_info_tick(SYMBOL)
        if t is None: raise RuntimeError("EURUSD tick unavailable")
        req={"action":mt5.TRADE_ACTION_DEAL,"symbol":SYMBOL,"volume":VOLUME,"type":mt5.ORDER_TYPE_BUY,"price":t.ask,"deviation":10,"magic":MAGIC,"comment":"DEXORZO-V8-SMOKE60","type_time":mt5.ORDER_TIME_GTC}
        x=send(req); ticket=getattr(x,"order",0) or getattr(x,"deal",0)
        print(f"OPENED DEMO TEST: ticket={ticket} volume={VOLUME} at {getattr(x,'price',t.ask)}")
        end=time.time()+SECONDS
        while time.time()<end:
            ps=[p for p in (mt5.positions_get(symbol=SYMBOL) or []) if int(getattr(p,"magic",0))==MAGIC]
            if not ps: print("Position disappeared before 60s."); return
            rem=max(0,int(end-time.time()))
            print(f"\rOpen {SECONDS-rem:02d}s | P/L {ps[0].profit:.2f} USD | remaining {rem:02d}s",end="",flush=True)
            time.sleep(1)
        print()
        ps=[p for p in (mt5.positions_get(symbol=SYMBOL) or []) if int(getattr(p,"magic",0))==MAGIC]
        if ps:
            p=ps[0]; t=mt5.symbol_info_tick(SYMBOL)
            req={"action":mt5.TRADE_ACTION_DEAL,"symbol":SYMBOL,"volume":p.volume,"type":mt5.ORDER_TYPE_SELL,"position":p.ticket,"price":t.bid,"deviation":10,"magic":MAGIC,"comment":"DEXORZO-V8-SMOKE60-CLOSE","type_time":mt5.ORDER_TIME_GTC}
            y=send(req); print(f"CLOSED DEMO TEST: ticket={p.ticket} retcode={y.retcode} final floating P/L={p.profit:.2f} USD")
        print("1-minute Demo execution smoke test completed.")
    finally: mt5.shutdown()
if __name__=="__main__": main()
