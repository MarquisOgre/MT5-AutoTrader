# V8.5.1 Hotfix

The V8.5 console failure was:

NameError: name 'controls' is not defined

The hotfix adds the file-based operator control handler and restores the constants referenced by the order layer.

Controls:
- STOP_V8_5_1 = halt and close bot positions
- PAUSE_V8_5_1 = block new entries
- RESUME_V8_5_1 = resume operation

This release remains DEMO ONLY and uses the real MT5 account balance/equity.
