import MetaTrader5 as mt5
from config import LOGIN,PASSWORD,SERVER
def connect():
    ok=mt5.initialize(login=LOGIN,password=PASSWORD,server=SERVER) if LOGIN and PASSWORD and SERVER else mt5.initialize()
    if not ok: raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
    account=mt5.account_info()
    if account is None: raise RuntimeError(f"Cannot read MT5 account: {mt5.last_error()}")
    terminal=mt5.terminal_info(); print(f"Connected: {account.name} | Login: {account.login} | Server: {account.server}")
    print(f"Balance: {account.balance:.2f} {account.currency} | Equity: {account.equity:.2f}")
    print(f"Trade allowed by terminal: {getattr(terminal,'trade_allowed',None)}"); return account
def disconnect(): mt5.shutdown()
