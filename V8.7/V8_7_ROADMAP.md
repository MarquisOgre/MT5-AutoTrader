# V8.7 — True Session-Aware Dynamic Market Engine

## Weekend
1. Skip FX before scanning.
2. Probe Crypto first.
3. Probe Metals and Indices as fallback.
4. Select the best qualifying markets up to 12.

## Weekday
1. Probe FX first.
2. Fill remaining slots with Crypto.
3. Fill remaining slots with Metals/Indices.

## Qualification
- symbol enabled/tradable
- current session gate where Python MT5 session metadata is available
- executable Bid/Ask
- recent M5 history
- acceptable spread
- valid ATR/activity

## Safety
Never force a trade solely to reach 12 selected markets.
