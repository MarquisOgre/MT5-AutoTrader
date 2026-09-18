import MetaTrader5 as mt5
from config import LOGIN, PASSWORD, SERVER

def connect():
    if LOGIN and PASSWORD and SERVER:
        ok = mt5.initialize(login=LOGIN, password=PASSWORD, server=SERVER)
    else:
        ok = mt5.initialize()
    if not ok:
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
    account = mt5.account_info()
    if account is None:
        raise RuntimeError(f"Account info unavailable: {mt5.last_error()}")
    print(f"Connected to {account.server} | Login {account.login} | Balance {account.balance:.2f} {account.currency}")
    return account

def disconnect():
    mt5.shutdown()
