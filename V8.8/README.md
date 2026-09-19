# MT5 AutoTrader V8.8 - Fast Session-Aware 24x7 M5

V8.8 keeps the V8.7 session-aware dynamic market architecture and fixes the slow scanner path observed on MetaQuotes-Demo.

## Fast scanner
- Weekend: FX is skipped; Crypto is prioritized, then Metals and Index.
- Weekday: FX is prioritized, then Crypto, Metals and Index.
- Uses `symbol_info_tick()` for the first executable-quote filter.
- Historical `copy_ticks_from()` calls are removed from market selection.
- Session metadata is only queried for FX; 24x7 classes do not wait on Python session APIs during weekend selection.
- `symbol_select()` is performed once during subscription/warm-up.
- M5 history is requested only after a fresh executable quote and acceptable spread.
- No trade is forced just to reach 12 selected markets.

## Safety
- MetaQuotes-Demo only.
- Real MT5 Balance/Equity.
- Risk 0.25% per entry.
- Daily loss guard 2%.
- Max open bot positions 3.
- Max total exposure 1%.
- STOP / PAUSE / RESUME retained.

## Run
Double-click `run_v8_8_fast_session_aware_24x7_m5.bat`.
