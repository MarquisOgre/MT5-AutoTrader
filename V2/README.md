# MT5 AutoTrader V2 — Six Strategy Research System

Adds six independent strategies, a regime/ensemble signal layer, risk controls, MT5 historical-data backtesting and reports.

### Six strategies
1. Trend Following — EMA 20/50 + ADX + pullback
2. Breakout — Donchian-style breakout + ATR
3. Mean Reversion — Bollinger Bands + RSI
4. Momentum — MACD + RSI
5. Volatility Expansion — ATR compression + breakout
6. Multi-Timeframe — H1 trend context + M15 entry

Default configuration is research/safe mode; no order is sent by default.
