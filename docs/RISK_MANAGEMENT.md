# Risk Management

The project uses risk-based position sizing in its execution versions rather than a fixed lot size. SL distance is derived from market volatility/ATR and volume is calculated against the configured risk budget.

Execution safeguards include spread limits, broker stop-distance validation, account/terminal trade permissions, one bot position per symbol and a MetaQuotes-Demo-only server guard.

Historical and demo results must not be interpreted as guarantees of future performance.
