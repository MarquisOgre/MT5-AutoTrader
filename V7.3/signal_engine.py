from data import get_rates,get_h1
from strategies import signal_frame
class SignalEngine:
 def __init__(self,config): self.config=config
 def get_signal(self,symbol):
  df=get_rates(symbol,500)
  if df is None:return None
  h1=get_h1(symbol,1500); strategies=self.config.get("enabled_strategies",{}).get(symbol,[])
  votes={"BUY":[],"SELL":[]}
  for name in strategies:
   s=signal_frame(df,name,h1).iloc[-2]["signal"]
   if s in votes:votes[s].append(name)
  req=int(self.config.get("filters",{}).get("require_signal_consensus",2))
  direction=None; used=[]
  if len(votes["BUY"])>=req and len(votes["BUY"])>len(votes["SELL"]): direction,used="BUY",votes["BUY"]
  elif len(votes["SELL"])>=req and len(votes["SELL"])>len(votes["BUY"]): direction,used="SELL",votes["SELL"]
  if not direction:return None
  row=df.iloc[-2]; atr=float(signal_frame(df,strategies[0],h1).iloc[-2]["atr"]) if strategies else 0
  return {"symbol":symbol,"direction":direction,"strategies":used,"entry_reference":float(row.close),"atr":atr,"time":row.time}
