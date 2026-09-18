# MT5 AutoTrader

Python-based MetaTrader 5 automated trading research and execution project.

## Current status

**Latest documented version: V7.1 — DEMO ONLY.**

The repository preserves the project's evolution from the initial V1 bot through V7.1, including research, backtesting, robustness testing, paper trading, and controlled MetaQuotes-Demo execution.

> Trading systems can lose money. Historical, paper, and demo results do not guarantee future performance.

## Version history

| Version | Stage | Main additions |
|---|---|---|
| V1 | Initial | EMA/RSI/breakout strategy, ATR SL/TP, risk controls, MT5 connection |
| V2 | Research | Six independent strategies, ensemble signals, historical backtesting |
| V3 | Research | Train/test validation and optimized precomputed signal/backtest engine |
| V4 | Research | Expanded research engine to 12 strategies |
| V5 | Research | Parameter robustness, cost-stress testing and walk-forward analysis |
| V5.1 | Research | Faster/fixed robustness workflow |
| V6 | Paper/Demo architecture | Real-time signal engine, risk manager, PAPER/DEMO separation |
| V6.1 | Paper | Live monitoring dashboard and signal-state tracking |
| V6.2 | Paper | Simulated positions, ATR SL/TP, P/L, win rate, drawdown and trade journal |
| V7 | Demo | MT5 Demo order execution, risk sizing, spread/stop checks and order validation |
| V7.1 | Demo | Fixed per-symbol spread configuration and MetaQuotes-Demo safety lock |

## Repository layout

```text
V1/       Initial MT5 Python bot
V2/       Six-strategy research
V3/       Train/test robust backtesting
V4/       Twelve-strategy research
V5/       Robustness + walk-forward research
V6/       Paper/demo architecture
V6.1/     Paper monitoring
V6.2/     Paper execution simulator
V7.1/     Current Demo execution build

docs/
  ARCHITECTURE.md
  MT5_SETUP.md
  RISK_MANAGEMENT.md
  TROUBLESHOOTING.md
  VERSION_HISTORY.md
```

## Strategy research

The project progressed from a single trend/breakout strategy into a multi-strategy framework. Researched signals include trend following, breakouts, mean reversion, momentum, volatility expansion, multi-timeframe context and later reversal/VWAP/ATR-style variants.

The research process deliberately separates historical testing, paper simulation and Demo execution.

## V5 research observations

During development, mean reversion was one of the strongest aggregate research candidates in the tested samples, but results varied by instrument. Cost-stress and walk-forward testing also showed that performance and stability varied with transaction costs and symbol.

These are historical observations from the development dataset and should not be treated as forecasts.

## V6 paper progression

### V6
Real-time market data + signal engine + risk framework, with PAPER mode sending zero orders.

### V6.1
Added a live console monitor showing scan status, signals and per-symbol state.

### V6.2
Added simulated positions with ATR-based SL/TP, live tick monitoring, paper P/L, wins/losses, win rate, drawdown and CSV trade records.

## V7.1 Demo execution

V7.1 can submit actual orders to the connected **MetaQuotes-Demo** account after execution checks.

Key controls include:

- M15 closed-candle signal processing
- Multi-strategy confirmation
- ATR-based SL/TP
- Risk-based volume calculation using MT5 profit estimation
- Per-symbol spread limits
- Broker minimum stop-distance checks
- `mt5.order_check()` before `mt5.order_send()`
- MetaQuotes-Demo-only safety guard
- Account and terminal trade-permission checks
- One bot position per symbol
- Demo trade CSV journal

### V7.1 bug fix

V7.0 attempted to convert the entire per-symbol spread-limit dictionary to a float. That produced:

```text
TypeError: float() argument must be a string or a real number, not 'dict'
```

V7.1 resolves the configured spread limit for the individual symbol.

## Setup

1. Install MetaTrader 5 desktop.
2. Log in to a demo account.
3. Install Python dependencies.
4. Confirm MT5 is connected and automated trading is allowed.
5. Review the relevant version directory.
6. For V7.1, run its Demo launcher only after confirming the server is MetaQuotes-Demo.

Example:

```bash
python -m pip install -r requirements.txt
```

## Security

Never commit:

- MT5 passwords
- API keys
- private tokens
- account secrets
- generated trading logs containing sensitive information

The repository's `.gitignore` excludes common credential and generated-report files.

## Development roadmap

Potential future work:

- stronger portfolio-level risk limits
- daily loss enforcement in the live execution loop
- persistent state and restart recovery
- current/session drawdown analytics
- R-multiple and trade-age dashboard
- broker filling-mode compatibility improvements
- richer execution journal
- additional validation and stress testing
- production-readiness review

## Disclaimer

This is a software/research project, not financial advice. Automated trading involves substantial risk. No strategy or version in this repository guarantees profits.

---
**MT5 AutoTrader — V1 → V7.1**
