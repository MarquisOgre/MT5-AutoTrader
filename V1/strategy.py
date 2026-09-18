from indicators import add_indicators
from config import EMA_FAST,EMA_SLOW,RSI_PERIOD,ATR_PERIOD,BREAKOUT_LOOKBACK,RSI_BUY_MIN,RSI_SELL_MAX
def get_signal(df):
    x=add_indicators(df,EMA_FAST,EMA_SLOW,RSI_PERIOD,ATR_PERIOD)
    if len(x)<BREAKOUT_LOOKBACK+5:return None,x
    c=x.iloc[-2]
    buy=c["ema_fast"]>c["ema_slow"] and c["close"]>c["ema_slow"] and c["rsi"]>=RSI_BUY_MIN and c["close"]>c["recent_high"]
    sell=c["ema_fast"]<c["ema_slow"] and c["close"]<c["ema_slow"] and c["rsi"]<=RSI_SELL_MAX and c["close"]<c["recent_low"]
    return ("BUY" if buy else "SELL" if sell else None),x
