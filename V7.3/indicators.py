import numpy as np

def ema(s,n): return s.ewm(span=n,adjust=False).mean()
def sma(s,n): return s.rolling(n).mean()
def rsi(s,n=14):
 d=s.diff(); gain=d.clip(lower=0); loss=-d.clip(upper=0)
 ag=gain.ewm(alpha=1/n,adjust=False,min_periods=n).mean()
 al=loss.ewm(alpha=1/n,adjust=False,min_periods=n).mean()
 rs=ag/al.replace(0,np.nan); return 100-100/(1+rs)
def atr(df,n=14):
 pc=df.close.shift(1); tr=np.maximum(df.high-df.low,np.maximum((df.high-pc).abs(),(df.low-pc).abs()))
 return tr.ewm(alpha=1/n,adjust=False,min_periods=n).mean()
def stochastic(df,n=14,smooth=3):
 lo=df.low.rolling(n).min(); hi=df.high.rolling(n).max(); k=100*(df.close-lo)/(hi-lo).replace(0,np.nan); return k,k.rolling(smooth).mean()
def enrich(df):
 x=df.copy(); x["ema20"]=ema(x.close,20); x["ema50"]=ema(x.close,50); x["rsi"]=rsi(x.close); x["atr"]=atr(x)
 mid=sma(x.close,20); sd=x.close.rolling(20).std(); x["bb_upper"]=mid+2*sd; x["bb_lower"]=mid-2*sd
 x["macd"]=ema(x.close,12)-ema(x.close,26); x["macd_signal"]=ema(x.macd,9); x["macd_hist"]=x.macd-x.macd_signal
 x["donchian_high20"]=x.high.shift(1).rolling(20).max(); x["donchian_low20"]=x.low.shift(1).rolling(20).min()
 x["stoch_k"],x["stoch_d"]=stochastic(x); x["vwap20"]=(x.close*x.tick_volume).rolling(20).sum()/x.tick_volume.rolling(20).sum().replace(0,np.nan)
 return x
