from indicators import enrich
STRATEGY_NAMES=["Trend Following","Breakout","Mean Reversion","Momentum","Volatility Expansion","Multi-Timeframe"]
def _trend(r):
    if r.ema20>r.ema50 and r.close>r.ema50 and r.adx>=20:return "BUY"
    if r.ema20<r.ema50 and r.close<r.ema50 and r.adx>=20:return "SELL"
def _breakout(r):
    if r.close>r.donchian_high and r.atr>0:return "BUY"
    if r.close<r.donchian_low and r.atr>0:return "SELL"
def _mean_reversion(r):
    if r.close<=r.bb_lower and r.rsi<=30:return "BUY"
    if r.close>=r.bb_upper and r.rsi>=70:return "SELL"
def _momentum(r):
    if r.macd_hist>0 and r.rsi>=55 and r.close>r.ema20:return "BUY"
    if r.macd_hist<0 and r.rsi<=45 and r.close<r.ema20:return "SELL"
def _volatility_expansion(r,p):
    if p is None:return None
    c=p.atr_fast<p.atr_slow*.75
    if c and r.close>r.donchian_high:return "BUY"
    if c and r.close<r.donchian_low:return "SELL"
def _mtf(r,h):
    if h is None:return None
    if h.ema20>h.ema50 and r.close>r.ema20 and r.rsi>=50:return "BUY"
    if h.ema20<h.ema50 and r.close<r.ema20 and r.rsi<=50:return "SELL"
def generate_signals(df,h1_df=None):
    x=enrich(df).dropna().reset_index(drop=True)
    if len(x)<250:return None,x
    i=len(x)-2; r=x.iloc[i]; p=x.iloc[i-1] if i>0 else None; h=None
    if h1_df is not None and len(h1_df)>220:
        h1=enrich(h1_df).dropna().reset_index(drop=True); eligible=h1[h1.time<=r.time]
        if len(eligible):h=eligible.iloc[-1]
    s={"Trend Following":_trend(r),"Breakout":_breakout(r),"Mean Reversion":_mean_reversion(r),"Momentum":_momentum(r),"Volatility Expansion":_volatility_expansion(r,p),"Multi-Timeframe":_mtf(r,h)}
    return s,x
def ensemble_signal(signals,min_score=2):
    b=sum(v=="BUY" for v in signals.values()); s=sum(v=="SELL" for v in signals.values())
    if b>=min_score and b>s:return "BUY",b,s
    if s>=min_score and s>b:return "SELL",b,s
    return None,b,s
