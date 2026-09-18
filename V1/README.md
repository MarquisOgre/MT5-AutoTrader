# MT5 Python AutoTrader

A modular MetaTrader 5 Python trading bot for research, backtesting, demo trading, and controlled live deployment.

## Important
This bot does NOT guarantee profit. Trading can lose money. Keep DRY_RUN=true and ENABLE_LIVE=false until the strategy has been independently backtested and demo-tested.

## Install
Install Python 3.10+ and MetaTrader 5 desktop, log into a demo account, then run run_test.bat or install requirements and run test_connection.py.

## Strategy
Initial strategy: EMA 20/50 trend filter, RSI 14 confirmation, 20-candle breakout, ATR stop, 1.8R target, spread filter, fractional risk sizing, maximum open positions and daily loss guard. Signals use the last closed candle.

## Development path
Historical backtesting → walk-forward testing → robustness testing → demo forward testing → logging/dashboard → controlled deployment.
