import pandas as pd
from indicators import enrich
def signal_frame(df,strategy,h1=None):
 x=enrich(df).reset_index(drop=True); x["signal"]=None
 if strategy=="Mean Reversion": buy=(x.close<=x.bb_lower)&(x.rsi<=30); sell=(x.close>=x.bb_upper)&(x.rsi>=70)
 elif strategy=="RSI Reversal": buy=(x.rsi.shift(1)<30)&(x.rsi>=30)&(x.close>x.close.shift(1)); sell=(x.rsi.shift(1)>70)&(x.rsi<=70)&(x.close<x.close.shift(1))
 elif strategy=="VWAP Mean Reversion":
  dist=(x.close-x.vwap20)/x.atr.replace(0,pd.NA); buy=(dist<=-1.5)&(x.rsi<40); sell=(dist>=1.5)&(x.rsi>60)
 elif strategy=="EMA Pullback":
  up=(x.ema20>x.ema50)&(x.close>x.ema50); dn=(x.ema20<x.ema50)&(x.close<x.ema50); buy=up&(x.low<=x.ema20)&(x.close>x.ema20); sell=dn&(x.high>=x.ema20)&(x.close<x.ema20)
 elif strategy=="Stochastic Reversal":
  up=(x.stoch_k.shift(1)<=x.stoch_d.shift(1))&(x.stoch_k>x.stoch_d); dn=(x.stoch_k.shift(1)>=x.stoch_d.shift(1))&(x.stoch_k<x.stoch_d); buy=up&(x.stoch_k<30); sell=dn&(x.stoch_k>70)
 elif strategy=="ATR Breakout":
  ex=x.atr>x.atr.rolling(50).mean()*1.2; buy=ex&(x.close>x.donchian_high20); sell=ex&(x.close<x.donchian_low20)
 else: buy=pd.Series(False,index=x.index); sell=pd.Series(False,index=x.index)
 x.loc[buy.fillna(False),"signal"]="BUY"; x.loc[sell.fillna(False),"signal"]="SELL"; return x
