# MT5 AutoTrader

Python-based MetaTrader 5 automated trading research and execution project.

## Current status

- V7.1: Demo-only execution with the spread-limit bug fixed.
- The bot connects to MetaQuotes-Demo and is designed to reject non-demo servers.
- Historical backtesting, robustness testing, paper trading, and demo execution are documented as separate stages.

## Version history

| Version | Stage | Main additions |
|---|---|---|
| V2 | Research | 6-strategy backtesting |
| V3 | Research | Train/test validation |
| V4 | Research | Expanded to 12 strategies |
| V5 | Research | Robustness, cost-stress and walk-forward testing |
| V5.1 | Research | Faster/fixed robustness engine |
| V6 | Paper | Paper/demo architecture and risk framework |
| V6.1 | Paper | Monitoring dashboard and signal monitoring |
| V6.2 | Paper | Simulated positions, ATR SL/TP and paper P/L |
| V7 | Demo | MT5 Demo order execution, risk sizing, SL/TP and order validation |
| V7.1 | Demo | Fixed per-symbol spread configuration and hardened demo execution |

## Strategies

The project has evolved to a multi-strategy signal engine. Strategies explored across versions include mean-reversion, stochastic reversal and additional trend/momentum/volatility style signals.

## Research results

Selected historical test observations from the development process:

- V3/V4 mean-reversion tests were positive on the aggregate research sample, while results varied by symbol.
- V5 cost-stress testing showed degraded but still positive aggregate mean-reversion research results at the tested cost multipliers.
- Walk-forward results varied substantially by symbol.

These are historical research observations, not guarantees of future performance.

## V7.1 features

- M15 closed-candle signal processing
- Multi-strategy confirmation
- ATR-based stop loss and take profit
- Risk-based position sizing
- Per-symbol spread limits
- Broker stop-distance validation
- `mt5.order_check()` before `mt5.order_send()`
- Demo-only server safety lock
- Account/terminal trade-permission checks
- One bot position per symbol
- Live floating and realized P/L tracking
- Win/loss tracking
- CSV trade journal
- Ctrl+C graceful shutdown

## Safety

V7/V7.1 are intended for MetaQuotes-Demo execution only. The bot is not a statement that a strategy is profitable or suitable for live capital. Live trading should require separate validation, monitoring, controls, and broker-specific testing.

## Windows setup

1. Install Python.
2. Install and log in to MetaTrader 5.
3. Confirm the terminal is connected to the intended demo account.
4. Install requirements:

```bash
python -m pip install -r requirements.txt
```

5. Start the demo bot:

```text
run_v7_demo.bat
```

## Configuration

Strategy and execution settings are stored in `strategy_config.json`. Keep credentials out of source control. Do not commit API keys, passwords or private account secrets.

## Project roadmap

Future versions can add stronger portfolio-level risk limits, daily loss protection, drawdown monitoring, trade lifecycle analytics, persistence/recovery, additional validation, and a production-readiness review.

---
Built during iterative MT5 AutoTrader research and development.
