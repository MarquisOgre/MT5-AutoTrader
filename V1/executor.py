import MetaTrader5 as mt5
from config import MAGIC_NUMBER,RR_RATIO,MAX_SPREAD_POINTS,DRY_RUN,ENABLE_LIVE,ATR_SL_MULTIPLIER
from risk import calculate_lot
def execute_signal(symbol,signal,atr):
    info=mt5.symbol_info(symbol); tick=mt5.symbol_info_tick(symbol)
    if not info or not tick:return False
    if not info.visible and not mt5.symbol_select(symbol,True):return False
    spread=(tick.ask-tick.bid)/info.point
    if spread>MAX_SPREAD_POINTS:return False
    entry=tick.ask if signal=="BUY" else tick.bid; sl=entry-ATR_SL_MULTIPLIER*atr if signal=="BUY" else entry+ATR_SL_MULTIPLIER*atr
    tp=entry+RR_RATIO*(entry-sl) if signal=="BUY" else entry-RR_RATIO*(sl-entry); typ=mt5.ORDER_TYPE_BUY if signal=="BUY" else mt5.ORDER_TYPE_SELL
    entry,sl,tp=round(entry,info.digits),round(sl,info.digits),round(tp,info.digits); lot=calculate_lot(symbol,entry,sl)
    if lot<=0:return False
    if DRY_RUN or not ENABLE_LIVE: print("DRY RUN / LIVE DISABLED — no order was sent."); return True
    req={"action":mt5.TRADE_ACTION_DEAL,"symbol":symbol,"volume":lot,"type":typ,"price":entry,"sl":sl,"tp":tp,"deviation":20,"magic":MAGIC_NUMBER,"comment":"Python AutoTrader","type_time":mt5.ORDER_TIME_GTC}
    check=mt5.order_check(req)
    if check is None or getattr(check,"retcode",0) not in (0,mt5.TRADE_RETCODE_DONE):return False
    result=mt5.order_send(req); return bool(result and result.retcode==mt5.TRADE_RETCODE_DONE)
