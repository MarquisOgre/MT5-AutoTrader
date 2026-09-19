#!/usr/bin/env python3
"""
DEXORZO Innovations
MT5 AutoTrader V8.8 - Fast Dynamic M5

Architecture:
- Uses fully closed M5 candles.
- Automatically discovers FX pairs available from the connected MT5 broker.
- Dynamically ranks live tradable pairs and selects up to 12 with the best
  current conditions (session open, fresh ticks, spread, ATR/activity).
- Runs ALL 12 strategies against every selected pair; no static pair/strategy map.
- Uses real MT5 Balance/Equity; no virtual balance.
- MetaQuotes-Demo safety lock remains enabled.
- Break-even, ATR trailing, optional partial TP, daily loss, exposure,
  restart recovery, STOP/PAUSE/RESUME, and journal retained.
"""

import csv, json, math, os, time
from datetime import datetime, timezone
from pathlib import Path

import MetaTrader5 as mt5
import pandas as pd

APP_TITLE = "MT5 AUTOTRADER V8.8 - FAST DYNAMIC M5"
BRAND = "Created By DEXORZO Innovations"
MAGIC = 762015
SCAN_SECONDS = 10
SESSION_REFRESH_SECONDS = 60
FAST_SCAN_NO_HISTORY = True
CRYPTO_PROBE_LIMIT = 220
METAL_PROBE_LIMIT = 80
INDEX_PROBE_LIMIT = 60
FX_PROBE_LIMIT = 60
SIGNAL_TIMEFRAME = mt5.TIMEFRAME_M5

# 20 common FX candidates. These are candidates only; the bot dynamically
# discovers which corresponding broker symbols actually exist and are tradable.
FX_CANDIDATES = [
    "EURUSD","GBPUSD","USDJPY","USDCHF","AUDUSD","USDCAD","NZDUSD",
    "EURGBP","EURJPY","EURCHF","EURAUD","EURCAD","EURNZD",
    "GBPJPY","GBPCHF","GBPAUD","GBPCAD","AUDJPY","AUDCAD","CADJPY"
]
CRYPTO_HINTS=("BTC","ETH","LTC","XRP","SOL","DOGE","ADA","DOT","BNB","AVAX","LINK","TRX","MATIC","USDT","USDC")
METAL_HINTS=("XAU","GOLD","XAG","SILVER","XPT","PLATINUM","XPD","PALLADIUM")
INDEX_HINTS=("US30","DJ30","DJI","NAS100","USTEC","SPX500","US500","GER40","DAX","UK100","FTSE","JP225","NIKKEI","AUS200","FRA40","STOXX")
MAX_SELECTED_PAIRS=12
MIN_REQUIRED_MARKETS=12

# Risk/execution controls.
RISK_PCT = 0.25
MAX_DAILY_LOSS_PCT = 2.0
MAX_OPEN_POSITIONS = 3
MAX_SYMBOL_POSITIONS = 1
MAX_TOTAL_EXPOSURE_PCT = 1.0
ATR_SL_MULT = 1.5
RR = 1.8
DEVIATION = 5
CONSENSUS = 2
COOLDOWN_MIN = 30

# Dynamic quality limits by asset class. Percentage limits avoid broker point-size differences.
DEFAULT_MAX_SPREAD_PCT={"FX":0.20,"CRYPTO":1.00,"METALS":0.60,"INDEX":0.60,"OTHER":0.80}
MIN_TICK_AGE_SECONDS={"FX":180,"CRYPTO":300,"METALS":300,"INDEX":300,"OTHER":300}
MIN_BARS=100
MIN_ATR_POINTS=0.0

STRATEGIES = [
    "Mean Reversion","RSI Reversal","VWAP Mean Reversion","EMA Pullback",
    "Stochastic Reversal","ATR Breakout","Trend Momentum","Bollinger Breakout",
    "MACD Crossover","Donchian Breakout","EMA Trend","ADX Trend"
]

MGMT = {
    "break_even":{"enabled":True,"trigger_r":1.0,"offset_points":2},
    "atr_trailing":{"enabled":True,"trigger_r":1.5,"atr_multiplier":1.0},
    "partial_take_profit":{"enabled":False,"trigger_r":1.0,"close_fraction":0.50},
    "max_time_in_trade_minutes":240
}

REPORT=Path("reports"); REPORT.mkdir(exist_ok=True)
RUNTIME=Path("runtime"); RUNTIME.mkdir(exist_ok=True)
TRADES_FILE=REPORT/"v8_8_dynamic_m5_trades.csv"
STATE_FILE=RUNTIME/"v8_8_day_state.json"
STOP_FILE=Path("STOP_V8_8")
PAUSE_FILE=Path("PAUSE_V8_7")
RESUME_FILE=Path("RESUME_V8_7")
# Runtime state for partial-take-profit management.
PARTIAL_STATE_FILE=RUNTIME/"v8_8_partial_state.json"

# Compatibility aliases used by the execution layer.
MAX_OPEN=MAX_OPEN_POSITIONS
MAX_SYMBOL=MAX_SYMBOL_POSITIONS
MAX_EXPOSURE_PCT=MAX_TOTAL_EXPOSURE_PCT
ATR_MULT=ATR_SL_MULT

def controls():
    """Read operator control files without stopping the scanner."""
    if STOP_FILE.exists():
        return "STOP"
    # Creating RESUME clears PAUSE and resumes normal operation.
    if RESUME_FILE.exists():
        try:
            RESUME_FILE.unlink()
        except OSError:
            pass
        try:
            PAUSE_FILE.unlink()
        except OSError:
            pass
        return "RUN"
    return "PAUSE" if PAUSE_FILE.exists() else "RUN"


FIELDS=["timestamp","event","symbol","direction","ticket","volume","entry","sl","tp","price",
        "profit","r_multiple","age_seconds","strategies","reason","retcode","mfe","mae","duration_seconds"]

def now_utc(): return datetime.now(timezone.utc)

def write_journal(row):
    new=not TRADES_FILE.exists()
    with TRADES_FILE.open("a",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS)
        if new: w.writeheader()
        w.writerow({k:row.get(k,"") for k in FIELDS})

def connect():
    if not mt5.initialize():
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
    a=mt5.account_info()
    if a is None: raise RuntimeError(f"MT5 account unavailable: {mt5.last_error()}")
    return a

def guard():
    a=mt5.account_info(); t=mt5.terminal_info()
    if a is None or t is None: raise RuntimeError("MT5 account/terminal information unavailable")
    if "MetaQuotes-Demo" not in str(a.server or ""):
        raise RuntimeError(f"SAFETY LOCK: V8.8 is restricted to MetaQuotes-Demo. Current server: {a.server}")
    if not bool(getattr(a,"trade_allowed",False)): raise RuntimeError("SAFETY LOCK: account trading is not allowed")
    if not bool(getattr(t,"trade_allowed",False)): raise RuntimeError("SAFETY LOCK: terminal Algo/automated trading is disabled")
    return a

def positions():
    p=mt5.positions_get()
    return [x for x in (p or []) if int(getattr(x,"magic",0))==MAGIC]

def norm_price(s,p):
    i=mt5.symbol_info(s)
    return round(float(p), int(i.digits)) if i else float(p)

def norm_volume(s,v):
    i=mt5.symbol_info(s)
    if not i: return None
    step=float(i.volume_step or .01); vmin=float(i.volume_min or step); vmax=float(i.volume_max or v)
    if v < vmin: return None
    v=min(v,vmax); v=math.floor(v/step+1e-12)*step
    if v < vmin: return None
    decimals=max(0,len(str(step).split(".")[-1].rstrip("0")))
    return round(v,decimals)

def risk_volume(s,side,entry,sl,risk_money):
    typ=mt5.ORDER_TYPE_BUY if side=="BUY" else mt5.ORDER_TYPE_SELL
    x=mt5.order_calc_profit(typ,s,1.0,entry,sl)
    if x is None or abs(float(x))<=0: return None
    return norm_volume(s,risk_money/abs(float(x)))

def filling_candidates(s):
    i=mt5.symbol_info(s)
    flag=int(getattr(i,"filling_mode",0)) if i else 0
    out=[]
    if flag&1: out.append(mt5.ORDER_FILLING_FOK)
    if flag&2: out.append(mt5.ORDER_FILLING_IOC)
    for x in (mt5.ORDER_FILLING_FOK,mt5.ORDER_FILLING_IOC,mt5.ORDER_FILLING_RETURN):
        if x not in out: out.append(x)
    return out

def checked_send(req):
    last=None
    for mode in filling_candidates(req["symbol"]):
        r=dict(req); r["type_filling"]=mode
        c=mt5.order_check(r); last=c
        if c is None: continue
        code=getattr(c,"retcode",None)
        if code==getattr(mt5,"TRADE_RETCODE_MARKET_CLOSED",10018):
            return None, "MARKET_CLOSED"
        if code==getattr(mt5,"TRADE_RETCODE_INVALID_FILL",10030):
            continue
        if code not in (0,1,mt5.TRADE_RETCODE_DONE):
            return None, f"ORDER_CHECK_{code}: {getattr(c,'comment','')}"
        result=mt5.order_send(r)
        if result is None: continue
        rcode=getattr(result,"retcode",None)
        if rcode==getattr(mt5,"TRADE_RETCODE_MARKET_CLOSED",10018):
            return None,"MARKET_CLOSED"
        if rcode==getattr(mt5,"TRADE_RETCODE_INVALID_FILL",10030):
            continue
        ok={mt5.TRADE_RETCODE_DONE,getattr(mt5,"TRADE_RETCODE_DONE_PARTIAL",-1)}
        if rcode in ok: return result,"OK"
        last=result
    if last is None: return None, f"ORDER_FAILED: {mt5.last_error()}"
    return None, f"ORDER_SEND_{getattr(last,'retcode','?')}: {getattr(last,'comment','')}"

def indicators(df):
    x=df.copy()
    x["ema20"]=x.close.ewm(span=20,adjust=False).mean()
    x["ema50"]=x.close.ewm(span=50,adjust=False).mean()
    d=x.close.diff(); g=d.clip(lower=0); l=-d.clip(upper=0)
    ag=g.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    al=l.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    x["rsi"]=100-100/(1+ag/al.replace(0,pd.NA))
    pc=x.close.shift(1)
    tr=pd.concat([(x.high-x.low),(x.high-pc).abs(),(x.low-pc).abs()],axis=1).max(axis=1)
    x["atr"]=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    mid=x.close.rolling(20).mean(); sd=x.close.rolling(20).std()
    x["bb_u"]=mid+2*sd; x["bb_l"]=mid-2*sd
    x["don_u"]=x.high.shift(1).rolling(20).max(); x["don_l"]=x.low.shift(1).rolling(20).min()
    lo=x.low.rolling(14).min(); hi=x.high.rolling(14).max()
    x["st_k"]=100*(x.close-lo)/(hi-lo).replace(0,pd.NA); x["st_d"]=x.st_k.rolling(3).mean()
    x["vwap20"]=(x.close*x.tick_volume).rolling(20).sum()/x.tick_volume.rolling(20).sum().replace(0,pd.NA)
    x["macd"]=x.close.ewm(span=12,adjust=False).mean()-x.close.ewm(span=26,adjust=False).mean()
    x["macd_sig"]=x.macd.ewm(span=9,adjust=False).mean()
    # ADX / directional movement.
    up=x.high.diff(); dn=-x.low.diff()
    plus=up.where((up>dn)&(up>0),0.0); minus=dn.where((dn>up)&(dn>0),0.0)
    atr=x["atr"].replace(0,pd.NA)
    x["plus_di"]=100*plus.ewm(alpha=1/14,adjust=False).mean()/atr
    x["minus_di"]=100*minus.ewm(alpha=1/14,adjust=False).mean()/atr
    dx=100*(x.plus_di-x.minus_di).abs()/(x.plus_di+x.minus_di).replace(0,pd.NA)
    x["adx"]=dx.ewm(alpha=1/14,adjust=False).mean()
    return x

def classify_symbol(name, info=None):
    u=str(name).upper()
    path=str(getattr(info,"path","") or "").upper() if info is not None else ""
    desc=str(getattr(info,"description","") or "").upper() if info is not None else ""
    cat=str(getattr(info,"category","") or "").upper() if info is not None else ""
    base=str(getattr(info,"currency_base","") or "").upper() if info is not None else ""
    # Broker metadata first; then robust name/description hints.
    if "CRYPTO" in path or "CRYPTO" in cat or any(h in u or h in desc for h in CRYPTO_HINTS): return "CRYPTO"
    if "METAL" in path or "METAL" in cat or any(h in u or h in desc for h in METAL_HINTS): return "METALS"
    if "INDEX" in path or "INDICES" in path or "INDEX" in cat or any(h in u or h in desc for h in INDEX_HINTS): return "INDEX"
    if "FOREX" in path or "FOREX" in cat or u in tuple(FX_CANDIDATES) or any(u.startswith(x) for x in FX_CANDIDATES): return "FX"
    # A conventional 6-character currency symbol is a useful fallback only when
    # both base/profit currencies look like fiat codes.
    profit=str(getattr(info,"currency_profit","") or "").upper() if info is not None else ""
    fiat={"USD","EUR","GBP","JPY","CHF","AUD","CAD","NZD","SGD","HKD","NOK","SEK","DKK","PLN","ZAR","MXN","TRY","CNH"}
    if len(base)==3 and len(profit)==3 and base in fiat and profit in fiat and base!=profit:
        return "FX"
    return "OTHER"

def is_weekend_utc():
    return datetime.now(timezone.utc).weekday() >= 5

def market_mode_label():
    return "WEEKEND / 24x7 MODE" if is_weekend_utc() else "WEEKDAY / FX MODE"

def session_priority(cls):
    # On weekends, do not waste scanner capacity on FX symbols that are
    # predictably closed. Crypto is first, then metals/indices where live.
    if is_weekend_utc():
        return {"CRYPTO":0,"METALS":1,"INDEX":2,"FX":99,"OTHER":99}.get(cls,99)
    return {"FX":0,"CRYPTO":1,"METALS":2,"INDEX":3,"OTHER":99}.get(cls,99)

def python_session_open(symbol):
    """Best-effort broker session check when the installed Python package exposes it.
    The official MQL5 session APIs use broker/server session schedules. Python package
    support can vary, so failure here is non-fatal and the live Bid/Ask test remains
    authoritative for executability. See MQL5 SymbolInfoSessionTrade documentation.
    """
    fn=getattr(mt5,"symbol_info_session_trade",None)
    if fn is None:
        return None
    # MQL5 ENUM_DAY_OF_WEEK: Sunday=0 ... Saturday=6.
    dow=(datetime.now(timezone.utc).weekday()+1)%7
    # Session timestamps are seconds from midnight; some brokers expose an end >= 24h.
    now_sec=datetime.now(timezone.utc).hour*3600+datetime.now(timezone.utc).minute*60+datetime.now(timezone.utc).second
    for i in range(16):
        try:
            r=fn(symbol,dow,i)
            if not r:
                break
            # Python bindings may return (from,to) or a named tuple.
            vals=list(r) if isinstance(r,(tuple,list)) else []
            if len(vals)<2: continue
            start=int(vals[0]); end=int(vals[1])
            if end==0 and start==0: return True
            if end<start: end += 86400
            t=now_sec
            if start<=t<=end: return True
        except Exception:
            break
    return False


def session_gate(symbol, cls):
    # Weekend: FX is predictably closed, while Crypto is 24x7. Do not call
    # broker session metadata for Crypto/Metals/Index here because some MT5
    # Python builds can make session-info calls unexpectedly slow.
    if is_weekend_utc() and cls=="FX":
        return False,"FX_WEEKEND_CLOSED"
    if cls!="FX":
        return True,"SESSION_OPEN"
    sess=python_session_open(symbol)
    if sess is False:
        return False,"SESSION_CLOSED"
    return True,"SESSION_OPEN"

def discover_markets():
    all_syms=mt5.symbols_get() or []
    counts={"FX":0,"CRYPTO":0,"METALS":0,"INDEX":0,"OTHER":0}
    buckets={"FX":[],"CRYPTO":[],"METALS":[],"INDEX":[]}
    for item in all_syms:
        name=str(item.name); cls=classify_symbol(name,item)
        counts[cls]=counts.get(cls,0)+1
        if cls not in buckets: continue
        mode=int(getattr(item,"trade_mode",0))
        if mode==getattr(mt5,"SYMBOL_TRADE_MODE_DISABLED",0): continue
        if is_weekend_utc() and cls=="FX":
            continue
        buckets[cls].append((name,item))

    # Selection order changes with the actual calendar. We never spend the
    # weekend probe budget on FX symbols that are predictably closed.
    ordered_classes=sorted(buckets,key=session_priority)
    limits={"FX":FX_PROBE_LIMIT,"CRYPTO":CRYPTO_PROBE_LIMIT,"METALS":METAL_PROBE_LIMIT,"INDEX":INDEX_PROBE_LIMIT}
    markets=[]
    for cls in ordered_classes:
        rows=sorted(buckets[cls],key=lambda x:(len(x[0]),x[0]))[:limits[cls]]
        for name,item in rows:
            markets.append(name)
    return markets,counts



def get_live_tick(symbol, max_age):
    """Fast executable quote check. Never request historical ticks during selection."""
    now=int(time.time())
    try:
        tick=mt5.symbol_info_tick(symbol)
    except Exception:
        return None,None,"NO_TICK_DATA"
    if tick is not None:
        bid=float(getattr(tick,"bid",0) or 0); ask=float(getattr(tick,"ask",0) or 0)
        ts=int(getattr(tick,"time",0) or 0)
        if bid>0 and ask>0 and ts>0:
            age=max(0,now-ts)
            if age<=max_age:
                return tick,age,"LIVE_TICK"
            return None,age,"STALE_TICK"
    return None,None,"NO_TICK_DATA"

def bar_diagnostic(symbol):
    try:
        raw=mt5.copy_rates_from_pos(symbol,SIGNAL_TIMEFRAME,0,20)
        if raw is None or len(raw)==0:
            return {"bar":"NONE","bar_age":None}
        last_ts=int(raw[-1]["time"]); age=max(0,int(time.time())-last_ts)
        return {"bar":"RECENT" if age<=900 else "STALE","bar_age":age}
    except Exception:
        return {"bar":"ERROR","bar_age":None}


def market_quality(symbol):
    try:
        info=mt5.symbol_info(symbol)
        if info is None:return None,"NO_SYMBOL"
        cls=classify_symbol(symbol,info)
        ok_session,session_reason=session_gate(symbol,cls)
        if not ok_session:return None,session_reason
        trade_mode=int(getattr(info,"trade_mode",0))
        if trade_mode==getattr(mt5,"SYMBOL_TRADE_MODE_DISABLED",0):return None,"TRADE_DISABLED"
        if trade_mode==getattr(mt5,"SYMBOL_TRADE_MODE_CLOSEONLY",3):return None,"CLOSE_ONLY"
        # Selection already subscribed to the probe universe. Avoid a second
        # symbol_select call here; it can be a blocking terminal/server call.
        tick,age_s,tick_source=get_live_tick(symbol,MIN_TICK_AGE_SECONDS.get(cls,300))
        if tick is None:
            if tick_source=="STALE_TICK": return None,"STALE_TICK_NO_EXECUTABLE_QUOTE"
            return None,"NO_RECENT_TICK"
        bid=float(getattr(tick,"bid",0) or 0); ask=float(getattr(tick,"ask",0) or 0)
        if bid<=0 or ask<=0:return None,"INVALID_TICK"
        mid=(ask+bid)/2
        if mid<=0:return None,"INVALID_MID"
        spread_pct=(ask-bid)/mid*100
        limit=DEFAULT_MAX_SPREAD_PCT.get(cls,DEFAULT_MAX_SPREAD_PCT["OTHER"])
        if spread_pct>limit:return None,f"SPREAD_GT_{limit:.2f}PCT"
        raw=mt5.copy_rates_from_pos(symbol,SIGNAL_TIMEFRAME,0,160)
        if raw is None or len(raw)<MIN_BARS:return None,"INSUFFICIENT_M5_DATA"
        df=pd.DataFrame(raw); df["time"]=pd.to_datetime(df["time"],unit="s")
        x=indicators(df); atr=float(x.iloc[-2].atr)
        if not math.isfinite(atr) or atr<=MIN_ATR_POINTS:return None,"INVALID_ATR"
        point=float(info.point or 0); atr_points=atr/point if point>0 else 0
        activity=float(df.tail(20).tick_volume.mean())
        if not math.isfinite(activity) or activity<=0:return None,"LOW_ACTIVITY"
        score=(math.log1p(max(activity,1))*math.log1p(max(atr_points,1)))/(max(spread_pct,0.01)*(1+age_s/300))
        return {"symbol":symbol,"asset_class":cls,"spread_pct":spread_pct,"atr":atr,"atr_points":atr_points,"activity":activity,"tick_age":age_s,"tick_source":tick_source,"score":score},"OK"
    except Exception as e:
        return None,"ERROR_"+type(e).__name__

def select_pairs():
    discovered,inventory=discover_markets(); good=[]; reasons={}; samples=[]
    total=len(discovered)
    # Subscribe to the entire current probe universe first. This gives the MT5
    # terminal a chance to populate live quotes before quality checks begin.
    for symbol in discovered:
        try: mt5.symbol_select(symbol,True)
        except Exception: pass
    # Small warm-up only; the process remains responsive and the dashboard can
    # report exactly which feed state is observed.
    time.sleep(2)
    for idx,symbol in enumerate(discovered,1):
        if idx==1 or idx%10==0:
            print(f"\rScanning {market_mode_label()}: {idx}/{total} ...",end="",flush=True)
        q,reason=market_quality(symbol)
        if q: good.append(q)
        else:
            reasons[reason]=reasons.get(reason,0)+1
            if len(samples)<12 and classify_symbol(symbol,mt5.symbol_info(symbol)) in ("CRYPTO","METALS","INDEX"):
                samples.append((symbol,reason,{"bar":"SKIPPED_FAST_SCAN","bar_age":None}))
    print(f"\rScanning {market_mode_label()}: {total}/{total} ... done.{' '*20}")
    groups={c:sorted([q for q in good if q["asset_class"]==c],key=lambda q:q["score"],reverse=True) for c in ("FX","CRYPTO","METALS","INDEX")}
    ordered=[]
    for cls in sorted(groups,key=session_priority): ordered.extend(groups[cls])
    return ordered[:MAX_SELECTED_PAIRS],discovered,reasons,inventory,samples

def signal_for(s):
    raw=mt5.copy_rates_from_pos(s,SIGNAL_TIMEFRAME,0,500)
    if raw is None or len(raw)<260:return None
    df=pd.DataFrame(raw)
    df["time"]=pd.to_datetime(df["time"],unit="s")
    x=indicators(df).reset_index(drop=True)
    i=len(x)-2
    row=x.iloc[i]; prev=x.iloc[i-1]
    votes={"BUY":[],"SELL":[]}
    for n in STRATEGIES:
        buy=sell=False
        if n=="Mean Reversion":
            buy=bool(row.close<=row.bb_l and row.rsi<=30); sell=bool(row.close>=row.bb_u and row.rsi>=70)
        elif n=="RSI Reversal":
            buy=bool(prev.rsi<30 and row.rsi>=30 and row.close>prev.close)
            sell=bool(prev.rsi>70 and row.rsi<=70 and row.close<prev.close)
        elif n=="VWAP Mean Reversion":
            dist=(row.close-row.vwap20)/row.atr if pd.notna(row.vwap20) and row.atr else 0
            buy=dist<=-1.5 and row.rsi<40; sell=dist>=1.5 and row.rsi>60
        elif n=="EMA Pullback":
            up=row.ema20>row.ema50; dn=row.ema20<row.ema50
            buy=up and row.low<=row.ema20 and row.close>row.ema20
            sell=dn and row.high>=row.ema20 and row.close<row.ema20
        elif n=="Stochastic Reversal":
            buy=prev.st_k<=prev.st_d and row.st_k>row.st_d and row.st_k<30
            sell=prev.st_k>=prev.st_d and row.st_k<row.st_d and row.st_k>70
        elif n=="ATR Breakout":
            avg=x.atr.rolling(50).mean().iloc[i]
            ex=pd.notna(avg) and row.atr>avg*1.2
            buy=ex and row.close>row.don_u; sell=ex and row.close<row.don_l
        elif n=="Trend Momentum":
            buy=row.ema20>row.ema50 and row.macd>row.macd_sig and row.rsi>50
            sell=row.ema20<row.ema50 and row.macd<row.macd_sig and row.rsi<50
        elif n=="Bollinger Breakout":
            buy=row.close>row.bb_u and row.atr>0; sell=row.close<row.bb_l and row.atr>0
        elif n=="MACD Crossover":
            buy=prev.macd<=prev.macd_sig and row.macd>row.macd_sig
            sell=prev.macd>=prev.macd_sig and row.macd<row.macd_sig
        elif n=="Donchian Breakout":
            buy=row.close>row.don_u; sell=row.close<row.don_l
        elif n=="EMA Trend":
            buy=row.ema20>row.ema50 and row.close>row.ema20
            sell=row.ema20<row.ema50 and row.close<row.ema20
        elif n=="ADX Trend":
            buy=row.adx>=20 and row.plus_di>row.minus_di
            sell=row.adx>=20 and row.minus_di>row.plus_di
        if buy:votes["BUY"].append(n)
        if sell:votes["SELL"].append(n)
    direction=None
    used=[]
    if len(votes["BUY"])>=CONSENSUS and len(votes["BUY"])>len(votes["SELL"]):
        direction="BUY"; used=votes["BUY"]
    elif len(votes["SELL"])>=CONSENSUS and len(votes["SELL"])>len(votes["BUY"]):
        direction="SELL"; used=votes["SELL"]
    if not direction or not pd.notna(row.atr) or row.atr<=0:return None
    return {"symbol":s,"direction":direction,"strategies":used,"atr":float(row.atr),"time":row.time}

def open_risk(ps):
    total=0
    for p in ps:
        if not p.sl: continue
        typ=mt5.ORDER_TYPE_BUY if p.type==mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_SELL
        z=mt5.order_calc_profit(typ,p.symbol,p.volume,p.price_open,p.sl)
        if z is not None: total+=abs(float(z))
    return total

def state_load():
    if STATE_FILE.exists():
        try: return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception: pass
    return {}

def day_start(a):
    st=state_load(); d=now_utc().date().isoformat()
    if st.get("date")!=d:
        st={"date":d,"day_start_equity":float(a.equity),"peak_equity":float(a.equity)}
        STATE_FILE.write_text(json.dumps(st,indent=2),encoding="utf-8")
    return float(st["day_start_equity"])

def update_peak(e):
    st=state_load(); st["peak_equity"]=max(float(st.get("peak_equity",e)),e)
    STATE_FILE.write_text(json.dumps(st,indent=2),encoding="utf-8")
    return st["peak_equity"]

def daily_pnl():
    a=mt5.account_info(); ps=positions()
    floating=sum(float(p.profit) for p in ps)
    st=state_load(); start=datetime.fromisoformat(st["date"]).replace(tzinfo=timezone.utc) if st.get("date") else now_utc()
    deals=mt5.history_deals_get(start,now_utc())
    realized=0
    for d in deals or []:
        if int(getattr(d,"magic",0))==MAGIC and getattr(d,"entry",None)==mt5.DEAL_ENTRY_OUT:
            realized+=float(getattr(d,"profit",0))+float(getattr(d,"swap",0))+float(getattr(d,"commission",0))
    return realized,floating

def daily_loss_pct(a):
    start=day_start(a); r,f=daily_pnl()
    return max(0,-(r+f))/start*100 if start else 0

def r_mult(p,current):
    if not p.sl: return None
    risk=abs(p.price_open-p.sl)
    if risk<=0:return None
    return ((current-p.price_open) if p.type==mt5.POSITION_TYPE_BUY else (p.price_open-current))/risk

def age(p):
    try: return max(0,time.time()-float(getattr(p,"time_msc",0))/1000) if getattr(p,"time_msc",0) else max(0,time.time()-float(p.time))
    except Exception:return 0

def modify_position(p,new_sl=None,new_tp=None):
    i=mt5.symbol_info(p.symbol); tick=mt5.symbol_info_tick(p.symbol)
    if not i or not tick:return False
    sl=p.sl if new_sl is None else norm_price(p.symbol,new_sl)
    tp=p.tp if new_tp is None else norm_price(p.symbol,new_tp)
    req={"action":mt5.TRADE_ACTION_SLTP,"symbol":p.symbol,"position":p.ticket,"sl":sl,"tp":tp,"magic":MAGIC,"comment":"DEXORZO-V8-MGMT"}
    result,msg=checked_send(req)
    return result is not None

def close_position(p,reason):
    tick=mt5.symbol_info_tick(p.symbol)
    if not tick:return False
    typ=mt5.ORDER_TYPE_SELL if p.type==mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
    price=tick.bid if p.type==mt5.POSITION_TYPE_BUY else tick.ask
    req={"action":mt5.TRADE_ACTION_DEAL,"symbol":p.symbol,"volume":p.volume,"type":typ,
         "position":p.ticket,"price":price,"deviation":DEVIATION,"magic":MAGIC,
         "comment":"DEXORZO-V8-CLOSE","type_time":mt5.ORDER_TIME_GTC}
    result,msg=checked_send(req)
    write_journal({"timestamp":now_utc().isoformat(),"event":"CLOSE","symbol":p.symbol,
                   "direction":"BUY" if p.type==mt5.POSITION_TYPE_BUY else "SELL",
                   "ticket":p.ticket,"volume":p.volume,"price":price,"profit":p.profit,
                   "r_multiple":r_mult(p,price),"age_seconds":int(age(p)),"reason":reason,
                   "retcode":getattr(result,"retcode","") if result else ""})
    return result is not None

def manage_positions():
    ps=positions()
    try:
        partial_state=json.loads(PARTIAL_STATE_FILE.read_text(encoding="utf-8")) if PARTIAL_STATE_FILE.exists() else {}
    except Exception:
        partial_state={}
    active_tickets={str(p.ticket) for p in ps}
    partial_state={k:v for k,v in partial_state.items() if k in active_tickets}
    for p in ps:
        tick=mt5.symbol_info_tick(p.symbol); info=mt5.symbol_info(p.symbol)
        if not tick or not info: continue
        cur=tick.bid if p.type==mt5.POSITION_TYPE_BUY else tick.ask
        r=r_mult(p,cur)
        # Break-even.
        if MGMT["break_even"]["enabled"] and r is not None and r>=float(MGMT["break_even"]["trigger_r"]):
            offset=float(MGMT["break_even"]["offset_points"])*info.point
            target=p.price_open+offset if p.type==mt5.POSITION_TYPE_BUY else p.price_open-offset
            improve=(p.sl==0) or (target>p.sl if p.type==mt5.POSITION_TYPE_BUY else target<p.sl)
            if improve: modify_position(p,target,p.tp)
        # Optional partial take-profit. Disabled by default.
        if MGMT["partial_take_profit"]["enabled"] and r is not None and r>=float(MGMT["partial_take_profit"]["trigger_r"]):
            key=str(p.ticket)
            if not partial_state.get(key):
                fraction=min(0.99,max(0.01,float(MGMT["partial_take_profit"]["close_fraction"])))
                close_volume=norm_volume(p.symbol,float(p.volume)*fraction)
                if close_volume is not None and close_volume < float(p.volume):
                    close_type=mt5.ORDER_TYPE_SELL if p.type==mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
                    close_price=tick.bid if p.type==mt5.POSITION_TYPE_BUY else tick.ask
                    req={"action":mt5.TRADE_ACTION_DEAL,"symbol":p.symbol,"volume":close_volume,"type":close_type,
                         "position":p.ticket,"price":close_price,"deviation":DEVIATION,"magic":MAGIC,
                         "comment":"DEXORZO-V8-PARTIAL","type_time":mt5.ORDER_TIME_GTC}
                    result,msg=checked_send(req)
                    if result is not None:
                        partial_state[key]=True
                        write_journal({"timestamp":now_utc().isoformat(),"event":"PARTIAL_TP",
                                       "symbol":p.symbol,"direction":"BUY" if p.type==mt5.POSITION_TYPE_BUY else "SELL",
                                       "ticket":p.ticket,"volume":close_volume,"price":close_price,
                                       "profit":p.profit,"r_multiple":r,"reason":"PARTIAL_TAKE_PROFIT",
                                       "retcode":getattr(result,"retcode","")})
        # ATR trailing stop.
        if MGMT["atr_trailing"]["enabled"] and r is not None and r>=float(MGMT["atr_trailing"]["trigger_r"]):
            raw=mt5.copy_rates_from_pos(p.symbol,SIGNAL_TIMEFRAME,0,80)
            if raw is not None and len(raw)>=30:
                df=indicators(pd.DataFrame(raw)); atr=float(df.iloc[-2].atr)
                dist=float(MGMT["atr_trailing"]["atr_multiplier"])*atr
                target=cur-dist if p.type==mt5.POSITION_TYPE_BUY else cur+dist
                improve=(p.sl==0) or (target>p.sl if p.type==mt5.POSITION_TYPE_BUY else target<p.sl)
                if improve: modify_position(p,target,p.tp)
        # Maximum time in trade.
        max_min=float(MGMT["max_time_in_trade_minutes"])
        if max_min>0 and age(p)>=max_min*60: close_position(p,"MAX_TIME_IN_TRADE")
    PARTIAL_STATE_FILE.write_text(json.dumps(partial_state,indent=2),encoding="utf-8")

def send_entry(sig,a):
    ps=positions(); s=sig["symbol"]; side=sig["direction"]
    if len(ps)>=MAX_OPEN:return False,"MAX_OPEN_POSITIONS"
    if sum(x.symbol==s for x in ps)>=MAX_SYMBOL:return False,"MAX_SYMBOL_POSITIONS"
    if daily_loss_pct(a)>=MAX_DAILY_LOSS_PCT:return False,"DAILY_LOSS_LIMIT"
    if open_risk(ps)+a.equity*RISK_PCT/100 > a.equity*MAX_EXPOSURE_PCT/100:return False,"TOTAL_EXPOSURE_LIMIT"
    i=mt5.symbol_info(s); t=mt5.symbol_info_tick(s)
    if not i or not t:return False,"MARKET_DATA"
    spread=(t.ask-t.bid)/i.point; lim=SPREADS.get(s,30)
    if spread>lim:return False,f"SPREAD {spread:.1f}>{lim:.1f}"
    entry=t.ask if side=="BUY" else t.bid; dist=ATR_MULT*sig["atr"]
    sl=entry-dist if side=="BUY" else entry+dist
    tp=entry+RR*dist if side=="BUY" else entry-RR*dist
    entry,sl,tp=[norm_price(s,x) for x in (entry,sl,tp)]
    min_dist=max(float(getattr(i,"trade_stops_level",0))*i.point,float(getattr(i,"trade_freeze_level",0))*i.point)
    if min_dist and (abs(entry-sl)<min_dist or abs(tp-entry)<min_dist):return False,"BROKER_STOP_FREEZE_DISTANCE"
    vol=risk_volume(s,side,entry,sl,a.equity*RISK_PCT/100)
    if vol is None:return False,"VOLUME_BELOW_BROKER_MIN"
    typ=mt5.ORDER_TYPE_BUY if side=="BUY" else mt5.ORDER_TYPE_SELL
    req={"action":mt5.TRADE_ACTION_DEAL,"symbol":s,"volume":vol,"type":typ,"price":entry,
         "sl":sl,"tp":tp,"deviation":DEVIATION,"magic":MAGIC,"comment":"DEXORZO-V8",
         "type_time":mt5.ORDER_TIME_GTC}
    result,msg=checked_send(req)
    if result is None:return False,msg
    ticket=getattr(result,"order",0) or getattr(result,"deal",0)
    write_journal({"timestamp":now_utc().isoformat(),"event":"OPEN","symbol":s,"direction":side,
                   "ticket":ticket,"volume":vol,"entry":entry,"sl":sl,"tp":tp,
                   "price":getattr(result,"price",entry),"strategies":"|".join(sig["strategies"]),
                   "retcode":result.retcode})
    return True,f"OPENED #{ticket} {s} {side} {vol}"

def dashboard(a,selected,states,last,error,reasons=None,scanned=0,inventory=None,samples=None):
    ps=positions(); peak=update_peak(float(a.equity)); dd=max(0,(peak-a.equity)/peak*100) if peak else 0
    os.system("cls")
    print("+"+"-"*80+"+")
    print("|"+"DEXORZO  V8.8  |  INTELLIGENT 24x7 DYNAMIC M5".center(80)+"|")
    print("|"+BRAND.center(80)+"|")
    print("+"+"-"*80+"+")
    print("|"+f"Server: {a.server}".ljust(40)+f"Balance: ${a.balance:,.2f}".ljust(40)+"|")
    print("|"+f"Equity: ${a.equity:,.2f}".ljust(40)+f"Daily P/L: ${sum(daily_pnl()):,.2f}".ljust(40)+"|")
    print("|"+f"Selected Markets: {len(selected)}/{MAX_SELECTED_PAIRS}".ljust(40)+f"Open Positions: {len(ps)}/{MAX_OPEN_POSITIONS}".ljust(40)+"|")
    print("|"+f"Open Risk: ${open_risk(ps):,.2f}".ljust(40)+f"Daily Loss: {daily_loss_pct(a):.2f}%/{MAX_DAILY_LOSS_PCT:.2f}%".ljust(40)+"|")
    print("|"+f"Session DD: {dd:.2f}%".ljust(40)+f"Strategies: {len(STRATEGIES)}/12".ljust(40)+"|")
    print("+"+"-"*80+"+")
    print("|"+f"24x7 MARKET INVENTORY  |  {market_mode_label()}".center(80)+"|")
    inv=inventory or {}
    invline=f"FX:{inv.get('FX',0)}  CRYPTO:{inv.get('CRYPTO',0)}  METALS:{inv.get('METALS',0)}  INDEX:{inv.get('INDEX',0)}  OTHER:{inv.get('OTHER',0)}"
    print("|"+invline.center(80)+"|")
    print("+"+"-"*80+"+")
    print("|"+"SESSION-AWARE DYNAMIC MARKET SELECTION".center(80)+"|")
    if selected:
        for q in selected:
            row=f"{q['symbol']:<14} {q['asset_class']:<7} spread={q['spread_pct']:>5.2f}% age={q['tick_age']:>3}s ATR={q['atr_points']:>8.1f} score={q['score']:>8.1f}"
            print("|"+row[:80].ljust(80)+"|")
    else:
        msg=("No qualifying markets right now. Crypto/24x7 markets are being prioritized." if is_weekend_utc()
             else "No qualifying markets right now. FX is prioritized while open.")
        print("|"+msg.ljust(80)+"|")
    if reasons:
        top=" | ".join(f"{k}:{v}" for k,v in sorted(reasons.items(),key=lambda x:-x[1])[:5])
        print("|"+f"Scanned: {scanned} | Rejections: {top}".ljust(80)[:80]+"|")
    if samples:
        print("|"+"LIVE FEED DIAGNOSTICS (sample)".center(80)+"|")
        for sym,reason,bar in samples[:6]:
            btxt=f"M5={bar.get('bar')} age={bar.get('bar_age') if bar.get('bar_age') is not None else '-'}s"
            print("|"+f"{sym:<18} {reason:<30} {btxt}"[:80].ljust(80)+"|")
    print("+"+"-"*80+"+")
    print("|"+"STATUS".center(80)+"|")
    for q in selected:
        s=q["symbol"]; print("|"+f"{s:<14}{q['asset_class']:<8}{states.get(s,'WAITING')}".ljust(80)+"|")
    if ps:
        print("+"+"-"*80+"+")
        print("|"+"OPEN BOT POSITIONS".center(80)+"|")
        print("|"+"Symbol Side Entry        Current      SL           TP        P/L       R    Age".ljust(80)+"|")
        for p in ps:
            t=mt5.symbol_info_tick(p.symbol); cur=(t.bid if p.type==mt5.POSITION_TYPE_BUY else t.ask) if t else 0
            rr=r_mult(p,cur); side="BUY" if p.type==mt5.POSITION_TYPE_BUY else "SELL"
            row=f"{p.symbol:<8} {side:<4} {p.price_open:<12.5f} {cur:<12.5f} {p.sl:<11.5f} {p.tp:<10.5f} ${p.profit:<8.2f} {rr if rr is not None else 0:>5.2f} {int(age(p)):>5}s"
            print("|"+row[:80].ljust(80)+"|")
    print("+"+"-"*80+"+")
    print("|"+f"Last Signal: {last}".ljust(40)+f"Last Error: {error or 'None'}".ljust(40)+"|")
    print("|"+f"Heartbeat: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Mode: {market_mode_label()}".ljust(80)+"|")
    print("|"+"Controls: STOP=halt/close | PAUSE=block entries | RESUME=resume".ljust(80)[:80]+"|")
    print("+"+"-"*80+"+")

def main():
    print(BRAND)
    a=connect(); a=guard(); day_start(a)
    states={}; seen={}; last="None"; error=""
    try:
        while True:
            a=guard(); ctl=controls(); ps=positions()
            if ctl=="STOP":
                for p in ps: close_position(p,"EMERGENCY_STOP")
                dashboard(a,[],states,last,"STOP_V8_8 active - halted",{},0,{},[])
                break
            manage_positions()
            selected,discovered,reasons,inventory,samples=select_pairs()
            selected_symbols={q["symbol"] for q in selected}
            states={s:("SELECTED" if s in selected_symbols else "NOT SELECTED") for s in discovered}
            if ctl=="PAUSE":
                for s in selected_symbols:
                    if not any(p.symbol==s for p in positions()): states[s]="PAUSED"
            else:
                for q in selected:
                    s=q["symbol"]
                    if any(p.symbol==s for p in positions()):continue
                    try:
                        sig=signal_for(s)
                        if not sig:continue
                        key=str(sig["time"])
                        if seen.get(s)==key:continue
                        seen[s]=key
                        ok,msg=send_entry(sig,a)
                        states[s]="OPENED "+sig["direction"] if ok else "ORDER BLOCKED"
                        if ok:
                            last=f"{s} {sig['direction']} | {', '.join(sig['strategies'])}"; error=""
                        else:error=f"{s}: {msg}"
                    except Exception as e:
                        states[s]="ERROR"; error=f"{s}: {e}"
            dashboard(a,selected,states,last,error,reasons,len(discovered),inventory,samples)
            time.sleep(SCAN_SECONDS)
    except KeyboardInterrupt:
        print("\\nV8.8 stopped by user.")
    finally: mt5.shutdown()

if __name__=="__main__": main()