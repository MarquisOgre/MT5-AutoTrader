# MT5 AutoTrader V8.10

## Resilient Live Feed / MT5 Connection Watchdog

V8.10 keeps the dynamic 24x7 M5 architecture and adds a non-fatal MT5 connection watchdog.

### New behavior
- If MetaTrader 5 is closed, disconnected, or account/terminal information becomes unavailable, the bot PAUSES instead of crashing.
- New entries are blocked while MT5 is unavailable.
- The terminal displays a clear warning and automatically retries the connection every 5 seconds.
- When MT5 is opened/reconnected to MetaQuotes-Demo, the bot automatically returns to LIVE operation.
- Wrong-server safety remains a hard stop.
- Temporary Algo Trading disablement is treated as PAUSED and rechecked automatically.
- If MT5 disappears during an execution cycle, the bot switches to the watchdog pause state rather than terminating.

### Controls
- STOP_V8_10 = emergency halt/close behavior
- PAUSE_V8_10 = operator pause/block entries
- RESUME_V8_10 = clear operator pause

### Run
1. Use the MetaQuotes-Demo account.
2. Install dependencies with `pip install -r requirements.txt`.
3. Start `run_v8_10.bat`.
4. If MT5 is accidentally closed, leave the bot running; reopen MT5 and reconnect. V8.10 will resume automatically.
