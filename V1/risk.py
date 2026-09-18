from datetime import datetime,timezone
import MetaTrader5 as mt5
from config import RISK_PER_TRADE,MAX_DAILY_LOSS
def count_bot_positions(magic):
    p=mt5.positions_get(); return sum(1 for x in p or [] if x.magic==magic)
def daily_loss_exceeded(magic):
    now=datetime.now(timezone.utc); start=datetime(now.year,now.month,now.day,tzinfo=timezone.utc); deals=mt5.history_deals_get(start,now); pnl=0.0
    for d in deals or []:
        if getattr(d,"magic",None)==magic:p+=float(getattr(d,"profit",0))+float(getattr(d,"swap",0))+float(getattr(d,"commission",0))
    a=mt5.account_info(); limit=(a.balance*MAX_DAILY_LOSS) if a and a.balance>0 else 0
    return (p<=-limit if limit else False),p
def calculate_lot(symbol,entry,stop,risk_fraction=RISK_PER_TRADE):
    info=mt5.symbol_info(symbol); account=mt5.account_info()
    if not info or not account:return 0.0
    distance=abs(entry-stop); ts=info.trade_tick_size; tv=info.trade_tick_value
    if distance<=0 or ts<=0 or tv<=0:return 0.0
    raw=(account.equity*risk_fraction)/((distance/ts)*tv); step=info.volume_step
    if step<=0:return 0.0
    lots=max(info.volume_min,min(info.volume_max,raw)); lots=int(lots/step)*step; return round(lots,8)
