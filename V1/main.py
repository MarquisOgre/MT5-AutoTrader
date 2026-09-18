import time
from datetime import datetime
from config import SYMBOLS,MAGIC_NUMBER,MAX_OPEN_POSITIONS,DRY_RUN,ENABLE_LIVE,TIMEFRAME
from mt5_connection import connect,disconnect
from market_data import get_rates
from strategy import get_signal
from risk import count_bot_positions,daily_loss_exceeded
from executor import execute_signal
import MetaTrader5 as mt5
def process_symbol(symbol):
    df=get_rates(symbol)
    if df is None:return
    signal,enriched=get_signal(df); last=enriched.iloc[-2]
    if not signal:return
    if count_bot_positions(MAGIC_NUMBER)>=MAX_OPEN_POSITIONS:return
    exceeded,pnl=daily_loss_exceeded(MAGIC_NUMBER)
    if exceeded:return
    execute_signal(symbol,signal,float(last.atr))
def main():
    connect(); last_minute=None
    try:
        while True:
            key=datetime.now().strftime("%Y-%m-%d %H:%M")
            if key!=last_minute:
                last_minute=key
                for s in SYMBOLS:
                    try:process_symbol(s)
                    except Exception as e:print(f"{s}: ERROR: {e}")
            time.sleep(1)
    except KeyboardInterrupt:print("Stopped by user.")
    finally:disconnect()
if __name__=="__main__":main()
