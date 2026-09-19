# V8.5 — Intelligent 24x7 Market Scanner

1. Discover the complete MT5 symbol universe.
2. Classify FX, Crypto, Metals and Indices from broker metadata and symbol/description.
3. Activate symbols in Market Watch before inspection.
4. Check actual trade mode.
5. Obtain fresh prices from tick history when direct tick data is stale.
6. Reject disabled/close-only, invalid tick, excessive spread, insufficient M5 data and low activity.
7. Rank qualifying instruments by live market quality.
8. Select up to 12: FX first while tradable; Crypto fills when FX is unavailable/insufficient; Metals/Indices are fallbacks.
9. Re-scan continuously.
10. Run all 12 strategies on fully closed M5 candles.

The engine targets 12 markets but never forces trades when fewer than 12 valid instruments are available.
