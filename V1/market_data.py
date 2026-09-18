import MetaTrader5 as mt5
import pandas as pd
from config import BARS,TIMEFRAME
TIMEFRAMES={"M1":mt5.TIMEFRAME_M1,"M5":mt5.TIMEFRAME_M5,"M15":mt5.TIMEFRAME_M15,"M30":mt5.TIMEFRAME_M30,"H1":mt5.TIMEFRAME_H1,"H4":mt5.TIMEFRAME_H4,"D1":mt5.TIMEFRAME_D1}
def get_rates(symbol,bars=BARS):
    rates=mt5.copy_rates_from_pos(symbol,TIMEFRAMES.get(TIMEFRAME,mt5.TIMEFRAME_M15),0,bars)
    if rates is None or len(rates)<100:return None
    df=pd.DataFrame(rates); df["time"]=pd.to_datetime(df["time"],unit="s"); return df
