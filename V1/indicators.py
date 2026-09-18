import numpy as np
def add_indicators(df, ema_fast=20, ema_slow=50, rsi_period=14, atr_period=14):
    x=df.copy(); x["ema_fast"]=x["close"].ewm(span=ema_fast,adjust=False).mean(); x["ema_slow"]=x["close"].ewm(span=ema_slow,adjust=False).mean()
    delta=x["close"].diff(); gain=delta.clip(lower=0); loss=-delta.clip(upper=0)
    avg_gain=gain.ewm(alpha=1/rsi_period,min_periods=rsi_period,adjust=False).mean(); avg_loss=loss.ewm(alpha=1/rsi_period,min_periods=rsi_period,adjust=False).mean()
    rs=avg_gain/avg_loss.replace(0,np.nan); x["rsi"]=100-(100/(1+rs)); prev=x["close"].shift(1)
    tr=np.maximum(x["high"]-x["low"],np.maximum((x["high"]-prev).abs(),(x["low"]-prev).abs()))
    x["atr"]=tr.ewm(alpha=1/atr_period,min_periods=atr_period,adjust=False).mean()
    x["recent_high"]=x["high"].shift(1).rolling(20).max(); x["recent_low"]=x["low"].shift(1).rolling(20).min()
    return x.dropna().reset_index(drop=True)
