import MetaTrader5 as mt5
print("Connecting to the MT5 terminal...")
if not mt5.initialize():raise SystemExit(f"FAILED: {mt5.last_error()}")
a=mt5.account_info(); t=mt5.terminal_info()
if a is None:raise SystemExit(f"Account read failed: {mt5.last_error()}")
print("=== MT5 CONNECTION TEST ==="); print("Login:",a.login); print("Server:",a.server); print("Name:",a.name); print("Balance:",a.balance,a.currency); print("Equity:",a.equity); print("Leverage:",a.leverage); print("Terminal connected:",t.connected if t else None); print("Terminal trade allowed:",t.trade_allowed if t else None)
print("=== SYMBOL TEST ===")
for s in ["EURUSD","GBPUSD","USDJPY","USDCHF"]:
 i=mt5.symbol_info(s); tick=mt5.symbol_info_tick(s); print(s,"available=",bool(i),"bid=",getattr(tick,"bid",None),"ask=",getattr(tick,"ask",None))
mt5.shutdown(); print("SUCCESS: Python can communicate with MT5.")
