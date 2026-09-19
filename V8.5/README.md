# MT5 AutoTrader V8.5 — Intelligent 24x7 Dynamic M5

V8.5 is the intelligent market scanner release. It discovers broker symbols from MT5, classifies FX, Crypto, Metals and Indices using broker metadata plus symbol/description hints, checks actual trade mode, retrieves fresh live ticks using symbol_info_tick and copy_ticks_from, measures spread/M5 ATR/activity/tick age, and dynamically selects up to 12 qualifying markets.

FX is preferred when tradable; Crypto fills weekend/closed-FX slots, followed by Metals/Indices. The dashboard reports inventory and rejection reasons. All 12 strategies evaluate selected markets on fully closed M5 candles. Real MT5 Balance/Equity is used and the MetaQuotes-Demo safety lock remains active.

Run run_v8_5_intelligent_24x7_m5.bat.
