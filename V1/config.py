import os
from dotenv import load_dotenv
load_dotenv()
def env_bool(name, default=False): return os.getenv(name, str(default)).strip().lower() in {"1","true","yes","on"}
def env_float(name, default):
    try: return float(os.getenv(name, default))
    except ValueError: return float(default)
def env_int(name, default):
    try: return int(os.getenv(name, default))
    except ValueError: return int(default)
LOGIN_RAW=os.getenv("MT5_LOGIN","").strip(); LOGIN=int(LOGIN_RAW) if LOGIN_RAW.isdigit() else None
PASSWORD=os.getenv("MT5_PASSWORD","").strip() or None; SERVER=os.getenv("MT5_SERVER","").strip() or None
TIMEFRAME=os.getenv("TIMEFRAME","M15").strip().upper()
SYMBOLS=[s.strip() for s in os.getenv("SYMBOLS","EURUSD,GBPUSD,USDJPY,USDCHF").split(",") if s.strip()]
RISK_PER_TRADE=env_float("RISK_PER_TRADE",0.005); MAX_DAILY_LOSS=env_float("MAX_DAILY_LOSS",0.02)
MAX_OPEN_POSITIONS=env_int("MAX_OPEN_POSITIONS",2); MAX_SPREAD_POINTS=env_int("MAX_SPREAD_POINTS",30)
RR_RATIO=env_float("RR_RATIO",1.8); MAGIC_NUMBER=env_int("MAGIC_NUMBER",26091801)
ENABLE_LIVE=env_bool("ENABLE_LIVE",False); DRY_RUN=env_bool("DRY_RUN",True)
EMA_FAST=20; EMA_SLOW=50; RSI_PERIOD=14; ATR_PERIOD=14; BREAKOUT_LOOKBACK=20
RSI_BUY_MIN=55; RSI_SELL_MAX=45; ATR_SL_MULTIPLIER=1.5; BARS=250
