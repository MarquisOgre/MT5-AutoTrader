# V8.8 Roadmap / Change Log

## Problem observed in V8.7
Weekend scanning could remain around `60/352` for a very long time. The selection path requested historical tick data and broker session metadata for symbols that did not have immediately executable data. Some MT5 terminal/server calls can block much longer than normal.

## V8.8 fix
1. Discover candidates.
2. Subscribe once.
3. Read current Bid/Ask.
4. Reject symbols without a fresh executable quote immediately.
5. Only then request M5 bars and calculate ATR/activity.
6. Rank and select up to 12 markets.

This improves scanner responsiveness. It does not force trades when no executable market qualifies.
