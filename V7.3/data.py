import MetaTrader5 as mt5
import pandas as pd
TIMEFRAME=mt5.TIMEFRAME_M15
def clean(r):
 if r is None or len(r)==0:return None
 d=pd.DataFrame(r); d["time"]=pd.to_datetime(d["time"],unit="s"); return d.sort_values("time").drop_duplicates("time").reset_index(drop=True)
def get_rates(symbol,bars=500):
 if not mt5.symbol_select(symbol,True): return None
 d=clean(mt5.copy_rates_from_pos(symbol,TIMEFRAME,0,bars)); return d if d is not None and len(d)>=260 else None
def get_h1(symbol,bars=1500):
 if not mt5.symbol_select(symbol,True): return None
 return clean(mt5.copy_rates_from_pos(symbol,mt5.TIMEFRAME_H1,0,bars))
