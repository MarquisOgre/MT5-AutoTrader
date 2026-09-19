# MT5 AutoTrader V8.9 — Live Market Discovery

V8.9 fixes the V8.8 qualification issue by using the terminal's current symbol_info bid/ask/time data before falling back to symbol_info_tick.

- Prefers current terminal quote data.
- Probes symbols in batches of 40.
- Uses time_msc for precise quote age.
- Only requests M5 history after a live executable quote passes.
- Shows live quote counts by asset class.
- Weekend: Crypto, then Metals, then Index; FX skipped.
- MetaQuotes-Demo only.
