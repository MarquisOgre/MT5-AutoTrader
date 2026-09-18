# Architecture

The system is organized as a pipeline:

1. MT5 connection and symbol data access.
2. Closed-candle market data preparation.
3. Multi-strategy signal generation.
4. Signal confirmation and execution filters.
5. Risk-based volume calculation.
6. ATR-derived SL/TP calculation.
7. Broker validation via order_check.
8. Demo execution via order_send.
9. Position/P&L tracking and CSV journaling.

V6.x stops at paper/simulated execution. V7.x can submit orders only when the safety checks identify a MetaQuotes-Demo server.
