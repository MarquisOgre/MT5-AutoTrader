# Troubleshooting

## No signal

WAITING means no qualifying setup has been produced on the current scan. Keep the terminal running while the strategy engine evaluates new closed candles.

## TypeError involving max_spread_points

V7.0 had a bug when the configuration stored per-symbol spread limits as a dictionary. V7.1 reads the limit for each symbol instead.

## Orders not opening

Check the dashboard and terminal logs for spread filters, broker stop-distance checks, order_check results, trade permissions and symbol visibility.

## Safety lock

V7.x intentionally rejects non-MetaQuotes-Demo servers. This is a deliberate execution safeguard.
