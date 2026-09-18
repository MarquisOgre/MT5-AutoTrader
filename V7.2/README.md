# DEXORZO Innovations — MT5 AutoTrader V7.2

**Created By DEXORZO Innovations**

## DEMO ONLY

V7.2 is the hardened Demo execution layer. It is hard-locked to `MetaQuotes-Demo` and rejects other servers.

### V7.2 controls
- 0.25% risk-per-trade target
- 2.00% daily-loss gate
- Maximum 3 bot positions
- Maximum 1 bot position per symbol
- Maximum 1.00% aggregate initial-SL exposure
- Persistent UTC day-start equity state
- Session peak-equity / drawdown tracking
- Restart recovery from server-side positions
- Position age, R-multiple and distance dashboard
- Robust filling-mode selection with order-check validation
- Broker stop/freeze-distance checks
- Spread limits per symbol
- Emergency STOP_V72 file blocks new entries
- CSV trade journal
- Fixed-width ASCII console borders for straight Windows rendering
- DEXORZO branding in the Python console, MT5 comments, launcher and docs

### Files
The runnable V7.2 package is distributed as the standalone ZIP. It contains the V7 signal engine dependencies plus the V7.2 execution layer.

`v7_2_execution.py` contains the embedded ASCII DEXORZO Innovations banner.

**Created By DEXORZO Innovations**
