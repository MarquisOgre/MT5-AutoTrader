# V8.9 Roadmap

V8.8 scanned the universe quickly but rejected almost every instrument as stale/no executable tick.

V8.9:
1. Uses symbol_info bid/ask/time_msc first.
2. Falls back to symbol_info_tick.
3. Probes in small batches.
4. Reports live quote counts and quote age.
5. Requests M5 history only after live quote validation.
