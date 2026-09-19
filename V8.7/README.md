# MT5 AutoTrader V8.7 — Session-Aware 24x7 Dynamic M5

V8.7 fixes the V8.6 weekend-selection failure.

- Weekend: FX symbols are excluded from the probe universe before scanning.
- Weekend priority: CRYPTO -> METALS -> INDEX.
- Weekday priority: FX -> CRYPTO -> METALS -> INDEX.
- Up to 12 markets are selected dynamically.
- MT5 Market Watch is warmed up before quality checks.
- Live executable Bid/Ask remains mandatory for an actual order.
- Recent M5 data, spread, ATR and activity are checked.
- 12 strategies remain active on every selected market.
- Real MT5 Balance/Equity and existing risk controls remain unchanged.
- Dashboard shows session mode and heartbeat so it cannot appear silently frozen.

A 12-market target is not permission to force trades. If the broker does not provide a live executable quote, that market remains rejected.
