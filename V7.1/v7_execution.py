import json, math, time, csv
from pathlib import Path
from datetime import datetime, timezone
import MetaTrader5 as mt5
from mt5_connection import connect, disconnect
from signal_engine import SignalEngine

CONFIG=json.loads(Path("strategy_config.json").read_text(encoding="utf-8"))
SYMBOLS=CONFIG["symbols"]; MAGIC=762001; SCAN_SECONDS=10
RISK_PCT=float(CONFIG.get("execution",{}).get("risk_pct",0.25))
ATR_SL_MULT=float(CONFIG.get("execution",{}).get("atr_sl_multiplier",1.5)); RR=float(CONFIG.get("execution",{}).get("risk_reward",2.0))
SPREAD_LIMITS=CONFIG.get("execution",{}).get("max_spread_points",30)
if isinstance(SPREAD_LIMITS,dict): SPREAD_LIMITS={str(k):float(v) for k,v in SPREAD_LIMITS.items()}
else: SPREAD_LIMITS=float(SPREAD_LIMITS)
DEVIATION=int(CONFIG.get("execution",{}).get("deviation_points",20))
REPORT=Path("reports"); REPORT.mkdir(exist_ok=True); TRADES_FILE=REPORT/"v7_live_demo_trades.csv"
FIELDS=["timestamp","event","symbol","direction","ticket","volume","entry","sl","tp","price","profit","strategies","reason","retcode"]
def write_trade(row):
    new=not TRADES_FILE.exists()
    with TRADES_FILE.open("a",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS)
        if new:w.writeheader()
        w.writerow({k:row.get(k,"") for k in FIELDS})
def norm_price(symbol,price):
    info=mt5.symbol_info(symbol); return round(float(price),int(info.digits))
def normalize_volume(symbol,volume):
    info=mt5.symbol_info(symbol); step=float(info.volume_step or .01); vmin=float(info.volume_min or step); vmax=float(info.volume_max or volume)
    v=math.floor(volume/step)*step; v=max(vmin,min(vmax,v)); decimals=max(0,len(str(step).split('.')[-1].rstrip('0'))); return round(v,decimals)
def calculate_volume(symbol,direction,entry,sl,risk_money):
    typ=mt5.ORDER_TYPE_BUY if direction=="BUY" else mt5.ORDER_TYPE_SELL; loss=mt5.order_calc_profit(typ,symbol,1.0,entry,sl)
    if loss is None or abs(float(loss))<=0:return None
    return normalize_volume(symbol,risk_money/abs(float(loss)))
def filling_mode(symbol):
    info=mt5.symbol_info(symbol); mode=getattr(info,"filling_mode",0)
    if mode&2:return mt5.ORDER_FILLING_IOC
    if mode&1:return mt5.ORDER_FILLING_FOK
    return mt5.ORDER_FILLING_RETURN
def demo_only_guard():
    account=mt5.account_info(); terminal=mt5.terminal_info()
    if account is None or terminal is None:raise RuntimeError("MT5 account/terminal information unavailable")
    server=str(account.server or "")
    if "MetaQuotes-Demo" not in server:raise RuntimeError(f"SAFETY LOCK: V7 only permits MetaQuotes-Demo. Current server: {server}")
    if not bool(getattr(account,"trade_allowed",False)):raise RuntimeError("SAFETY LOCK: trading is not allowed for this MT5 account")
    if not bool(getattr(terminal,"trade_allowed",False)):raise RuntimeError("SAFETY LOCK: terminal Algo/automated trading is disabled")
    return account
def get_our_positions():
    p=mt5.positions_get(); return [x for x in p or [] if int(getattr(x,"magic",0))==MAGIC]
def already_trading_symbol(symbol):return any(p.symbol==symbol for p in get_our_positions())
def send_entry(signal,account):
    symbol=signal["symbol"]; direction=signal["direction"]; info=mt5.symbol_info(symbol); tick=mt5.symbol_info_tick(symbol)
    if info is None or tick is None:return False,"market data unavailable"
    if not info.visible and not mt5.symbol_select(symbol,True):return False,"symbol not visible"
    spread=(tick.ask-tick.bid)/info.point; limit=float(SPREAD_LIMITS.get(symbol,30)) if isinstance(SPREAD_LIMITS,dict) else float(SPREAD_LIMITS)
    if spread>limit:return False,f"spread {spread:.1f} > {limit:.1f}"
    entry=tick.ask if direction=="BUY" else tick.bid; atr=float(signal.get("atr",0))
    if atr<=0:return False,"ATR unavailable"
    dist=ATR_SL_MULT*atr
    if direction=="BUY":sl,tp,typ=entry-dist,entry+RR*dist,mt5.ORDER_TYPE_BUY
    else:sl,tp,typ=entry+dist,entry-RR*dist,mt5.ORDER_TYPE_SELL
    entry,sl,tp=[norm_price(symbol,x) for x in (entry,sl,tp)]
    min_stop=float(getattr(info,"trade_stops_level",0))*info.point
    if min_stop and abs(entry-sl)<min_stop:return False,"SL violates broker minimum stop distance"
    if min_stop and abs(tp-entry)<min_stop:return False,"TP violates broker minimum stop distance"
    risk_money=float(account.balance)*RISK_PCT/100; volume=calculate_volume(symbol,direction,entry,sl,risk_money)
    if volume is None:return False,"could not calculate risk-based volume"
    request={"action":mt5.TRADE_ACTION_DEAL,"symbol":symbol,"volume":volume,"type":typ,"price":entry,"sl":sl,"tp":tp,"deviation":DEVIATION,"magic":MAGIC,"comment":"MT5AT-V7.1","type_time":mt5.ORDER_TIME_GTC,"type_filling":filling_mode(symbol)}
    check=mt5.order_check(request)
    if check is None:return False,f"order_check unavailable: {mt5.last_error()}"
    if getattr(check,"retcode",0) not in (0,mt5.TRADE_RETCODE_DONE):return False,f"order_check retcode={check.retcode} {getattr(check,'comment','')}"
    result=mt5.order_send(request)
    if result is None:return False,f"order_send returned None: {mt5.last_error()}"
    ok={mt5.TRADE_RETCODE_DONE,getattr(mt5,"TRADE_RETCODE_DONE_PARTIAL",-1)}
    if result.retcode not in ok:return False,f"order_send retcode={result.retcode} {getattr(result,'comment','')}"
    ticket=getattr(result,"order",0) or getattr(result,"deal",0)
    write_trade({"timestamp":datetime.now(timezone.utc).isoformat(),"event":"OPEN","symbol":symbol,"direction":direction,"ticket":ticket,"volume":volume,"entry":entry,"sl":sl,"tp":tp,"price":result.price,"strategies":"|".join(signal.get("strategies",[])),"retcode":result.retcode})
    return True,f"OPENED ticket={ticket} volume={volume} entry={result.price}
def main():
    connect(); account=demo_only_guard(); print(f"V7.1 safety lock passed: {account.server}")
    engine=SignalEngine(CONFIG); states={s:"WAITING" for s in SYMBOLS}; seen={}; last="None"; last_error=""
    try:
        while True:
            account=demo_only_guard()
            for symbol in SYMBOLS:
                if already_trading_symbol(symbol):states[symbol]="DEMO POSITION OPEN"; continue
                try:
                    signal=engine.get_signal(symbol)
                    if not signal:states[symbol]="WAITING"; continue
                    key=f"{symbol}:{signal['time']}"
                    if seen.get(symbol)==key:states[symbol]="SIGNAL SEEN"; continue
                    seen[symbol]=key; ok,msg=send_entry(signal,account)
                    if ok:states[symbol]=f"DEMO {signal['direction']} OPEN"; last=f"{symbol} {signal['direction']} | {', '.join(signal.get('strategies',[]))}"; last_error=""
                    else:states[symbol]="ORDER BLOCKED"; last_error=f"{symbol}: {msg}"
                except Exception as exc:states[symbol]="ERROR"; last_error=f"{symbol}: {exc}"
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"|",account.server,"|",[(s,states[s]) for s in SYMBOLS],"|",last,"|",last_error)
            time.sleep(SCAN_SECONDS)
    except KeyboardInterrupt:print("\nV7.1 stopped by user.")
    finally:disconnect()
if __name__=="__main__":main()
