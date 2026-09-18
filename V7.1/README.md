# MT5 AutoTrader V7.1 — DEMO ONLY

Corrected V7 build.

## V7.1 fix
Execution configuration stores spread limits per symbol. V7.0 incorrectly converted the entire dictionary to a float, causing a TypeError. V7.1 reads the limit for the individual symbol.

## Safety
- MetaQuotes-Demo server only.
- Refuses non-MetaQuotes-Demo servers.
- Uses order_check() before order_send().
- Can place actual orders on the DEMO account.
- No live/real-server execution is permitted by the safety guard.

Run: run_v7_demo.bat
