#!/usr/bin/env python3
"""
DEXORZO Innovations
MT5 AutoTrader V7.3 - DEMO ONLY

V7.3 UI release retains risk/lifecycle controls on top of the V7.1 execution engine.
This build is hard-locked to MetaQuotes-Demo servers.
"""

import csv
import json
import math
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import MetaTrader5 as mt5

from mt5_connection import connect, disconnect
from signal_engine import SignalEngine

# ============================================================================
# DEXORZO INNOVATIONS - BRAND / SAFETY
# ============================================================================
DEXORZO_BANNER = r"""
+--------------------------------------------------------------------------------+
|      _______   ________  __    __   ______   _______   ________   ______       |
|                                                                                |
|     |       \ |        \|  \  |  \ /      \ |       \ |        \ /      \      |
|     | $$$$$$$\| $$$$$$$$| $$  | $$|  $$$$$$\| $$$$$$$\ \$$$$$$$$|  $$$$$$\     |
|     | $$  | $$| $$__     \$$\/  $$| $$  | $$| $$__| $$    /  $$ | $$  | $$     |
|     | $$  | $$| $$  \     >$$  $$ | $$  | $$| $$    $$   /  $$  | $$  | $$     |
|     | $$  | $$| $$$$$    /  $$$$\ | $$  | $$| $$$$$$$\  /  $$   | $$  | $$     |
|     | $$__/ $$| $$_____ |  $$ \$$\| $$__/ $$| $$  | $$ /  $$___ | $$__/ $$     |
|     | $$    $$| $$     \| $$  | $$ \$$    $$| $$  | $$|  $$    \ \$$    $$     |
|      \$$$$$$$  \$$$$$$$$ \$$   \$$  \$$$$$$  \$$   \$$ \$$$$$$$$  \$$$$$$      |
|                                                                                |
|                                                                                |
+--------------------------------------------------------------------------------+
"""

APP_TITLE = "MT5 AUTOTRADER V7.3 - DEMO ONLY"
BRAND = "Created By DEXORZO Innovations"
MAGIC = 762003
SCAN_SECONDS = 10

# Windows console ANSI colors.
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
YELLOW = "\033[33m"
RESET = "\033[0m"

CONFIG = json.loads(Path("strategy_config.json").read_text(encoding="utf-8"))
SYMBOLS = list(CONFIG["symbols"])
if "USDCAD" not in SYMBOLS:
    SYMBOLS.append("USDCAD")
RISK_CFG = CONFIG.get("risk", {})
EXEC_CFG = CONFIG.get("execution", {})
FILTER_CFG = CONFIG.get("filters", {})

RISK_PCT = float(RISK_CFG.get("risk_per_trade_pct", EXEC_CFG.get("risk_pct", 0.25)))
MAX_DAILY_LOSS_PCT = float(RISK_CFG.get("max_daily_loss_pct", 2.0))
MAX_OPEN_POSITIONS = int(RISK_CFG.get("max_open_positions", 3))
MAX_SYMBOL_POSITIONS = int(RISK_CFG.get("max_symbol_positions", 1))
MAX_TOTAL_EXPOSURE_PCT = float(RISK_CFG.get("max_total_exposure_pct", 1.0))
ATR_SL_MULT = float(EXEC_CFG.get("atr_sl_multiplier", 1.5))
RR = float(EXEC_CFG.get("risk_reward", 1.8))
DEVIATION = int(EXEC_CFG.get("deviation_points", EXEC_CFG.get("slippage_points", 2)))
SPREAD_LIMITS = EXEC_CFG.get("max_spread_points", 30)
if isinstance(SPREAD_LIMITS, dict):
    SPREAD_LIMITS = {str(k): float(v) for k, v in SPREAD_LIMITS.items()}
else:
    SPREAD_LIMITS = float(SPREAD_LIMITS)
COOLDOWN_MINUTES = int(FILTER_CFG.get("cooldown_minutes", 30))

POSITION_OPEN_TIMES = {}

REPORT = Path("reports")
RUNTIME = Path("runtime")
REPORT.mkdir(exist_ok=True)
RUNTIME.mkdir(exist_ok=True)
TRADES_FILE = REPORT / "v7_3_demo_trades.csv"
DAY_STATE_FILE = RUNTIME / "day_start_equity.json"
STOP_FILE = Path("STOP_V73")

FIELDS = [
    "timestamp", "event", "symbol", "direction", "ticket", "volume",
    "entry", "sl", "tp", "price", "profit", "r_multiple", "age_minutes",
    "strategies", "reason", "retcode"
]


def write_trade(row):
    new = not TRADES_FILE.exists()
    with TRADES_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in FIELDS})


def utc_now():
    return datetime.now(timezone.utc)


def clear_screen():
    """Clear the terminal before every dashboard refresh."""
    os.system("cls" if os.name == "nt" else "clear")


def norm_price(symbol, price):
    info = mt5.symbol_info(symbol)
    return round(float(price), int(info.digits))


def normalize_volume_down(symbol, volume):
    info = mt5.symbol_info(symbol)
    if info is None:
        return None
    step = float(info.volume_step or 0.01)
    vmin = float(info.volume_min or step)
    vmax = float(info.volume_max or volume)
    if volume < vmin:
        return None
    volume = min(volume, vmax)
    volume = math.floor(volume / step + 1e-12) * step
    if volume < vmin:
        return None
    decimals = max(0, len(str(step).split(".")[-1].rstrip("0")))
    return round(volume, decimals)


def calculate_volume(symbol, direction, entry, sl, risk_money):
    order_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
    one_lot_loss = mt5.order_calc_profit(order_type, symbol, 1.0, entry, sl)
    if one_lot_loss is None:
        return None
    loss_per_lot = abs(float(one_lot_loss))
    if loss_per_lot <= 0:
        return None
    return normalize_volume_down(symbol, risk_money / loss_per_lot)


def demo_only_guard():
    account = mt5.account_info()
    terminal = mt5.terminal_info()
    if account is None or terminal is None:
        raise RuntimeError("MT5 account/terminal information unavailable")
    server = str(account.server or "")
    if "MetaQuotes-Demo" not in server:
        raise RuntimeError(
            f"SAFETY LOCK: V7.3 only permits MetaQuotes-Demo. Current server: {server}"
        )
    if not bool(getattr(account, "trade_allowed", False)):
        raise RuntimeError("SAFETY LOCK: account trading is not allowed")
    if not bool(getattr(terminal, "trade_allowed", False)):
        raise RuntimeError("SAFETY LOCK: terminal Algo/automated trading is disabled")
    return account


def get_our_positions():
    positions = mt5.positions_get()
    if positions is None:
        return []
    return [p for p in positions if int(getattr(p, "magic", 0)) == MAGIC]


def position_direction(position):
    return "BUY" if position.type == mt5.POSITION_TYPE_BUY else "SELL"


def position_r_multiple(position):
    if not position.sl or not position.price_open:
        return None
    direction = position_direction(position)
    risk_distance = abs(float(position.price_open) - float(position.sl))
    if risk_distance <= 0:
        return None
    tick = mt5.symbol_info_tick(position.symbol)
    if tick is None:
        return None
    current = tick.bid if direction == "BUY" else tick.ask
    reward_distance = (current - position.price_open) if direction == "BUY" else (position.price_open - current)
    return reward_distance / risk_distance


def position_risk_money(position):
    if not position.sl or not position.price_open:
        return 0.0
    order_type = mt5.ORDER_TYPE_BUY if position.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_SELL
    loss = mt5.order_calc_profit(order_type, position.symbol, float(position.volume), float(position.price_open), float(position.sl))
    return abs(float(loss)) if loss is not None else 0.0


def total_open_risk(positions):
    return sum(position_risk_money(p) for p in positions)


def current_session_drawdown(equity):
    state = load_runtime_state()
    peak = float(state.get("session_peak_equity", equity))
    if equity > peak:
        peak = equity
        state["session_peak_equity"] = peak
        save_runtime_state(state)
    return max(0.0, (peak - equity) / peak * 100.0) if peak else 0.0


def load_runtime_state():
    if DAY_STATE_FILE.exists():
        try:
            return json.loads(DAY_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_runtime_state(state):
    DAY_STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def get_day_start_equity(account):
    state = load_runtime_state()
    today = utc_now().date().isoformat()
    if state.get("date") != today:
        state = {"date": today, "day_start_equity": float(account.equity), "session_peak_equity": float(account.equity)}
        save_runtime_state(state)
    elif "day_start_equity" not in state:
        state["day_start_equity"] = float(account.equity)
        state.setdefault("session_peak_equity", float(account.equity))
        save_runtime_state(state)
    return float(state["day_start_equity"])


def daily_realized(account=None):
    now = utc_now()
    start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    deals = mt5.history_deals_get(start, now)
    if deals is None:
        return 0.0
    total = 0.0
    for d in deals:
        if int(getattr(d, "magic", 0)) != MAGIC:
            continue
        if getattr(d, "entry", None) != mt5.DEAL_ENTRY_OUT:
            continue
        total += float(getattr(d, "profit", 0.0)) + float(getattr(d, "swap", 0.0)) + float(getattr(d, "commission", 0.0))
    return total


def daily_stats():
    now = utc_now()
    start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    deals = mt5.history_deals_get(start, now)
    realized = wins = losses = 0.0
    win_count = loss_count = 0
    if deals:
        for d in deals:
            if int(getattr(d, "magic", 0)) != MAGIC or getattr(d, "entry", None) != mt5.DEAL_ENTRY_OUT:
                continue
            pnl = float(getattr(d, "profit", 0.0)) + float(getattr(d, "swap", 0.0)) + float(getattr(d, "commission", 0.0))
            realized += pnl
            if pnl > 0:
                wins += pnl
                win_count += 1
            elif pnl < 0:
                losses += pnl
                loss_count += 1
    return realized, win_count, loss_count, wins, losses


def daily_loss_pct(account):
    day_start = get_day_start_equity(account)
    realized = daily_realized(account)
    floating = sum(float(p.profit) for p in get_our_positions())
    loss = max(0.0, -(realized + floating))
    return (loss / day_start * 100.0) if day_start else 0.0


def emergency_stop_active():
    return STOP_FILE.exists()


def cooldown_ok(symbol, signal_time, seen):
    last = seen.get(symbol)
    if last is None:
        return True
    try:
        if isinstance(signal_time, str):
            current = datetime.fromisoformat(signal_time)
        else:
            current = signal_time.to_pydatetime() if hasattr(signal_time, "to_pydatetime") else signal_time
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        return (current - last).total_seconds() >= COOLDOWN_MINUTES * 60
    except Exception:
        return True


def supported_filling_modes(symbol):
    info = mt5.symbol_info(symbol)
    candidates = []
    broker_flags = int(getattr(info, "filling_mode", 0)) if info else 0
    # Keep RETURN as a final fallback; order_check decides whether the request is valid.
    if broker_flags & 1:
        candidates.append(mt5.ORDER_FILLING_FOK)
    if broker_flags & 2:
        candidates.append(mt5.ORDER_FILLING_IOC)
    candidates.extend([mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_RETURN])
    out = []
    for mode in candidates:
        if mode not in out:
            out.append(mode)
    return out


def check_order_with_filling(request):
    last = None
    for mode in supported_filling_modes(request["symbol"]):
        candidate = dict(request)
        candidate["type_filling"] = mode
        check = mt5.order_check(candidate)
        last = check
        if check is not None and getattr(check, "retcode", None) in (0, mt5.TRADE_RETCODE_DONE):
            return candidate, check
    return None, last


def send_checked_order(request):
    final_request, check = check_order_with_filling(request)
    if final_request is None:
        detail = "order_check failed"
        if check is not None:
            detail += f" retcode={getattr(check,'retcode','?')} {getattr(check,'comment','')}"
        else:
            detail += f": {mt5.last_error()}"
        return None, detail
    result = mt5.order_send(final_request)
    if result is None:
        return None, f"order_send returned None: {mt5.last_error()}"
    ok_codes = {mt5.TRADE_RETCODE_DONE, getattr(mt5, "TRADE_RETCODE_DONE_PARTIAL", -1)}
    if result.retcode not in ok_codes:
        return result, f"order_send retcode={result.retcode} {getattr(result,'comment','')}"
    return result, "OK"


def send_entry(signal, account, positions):
    symbol = signal["symbol"]
    direction = signal["direction"]
    if len(positions) >= MAX_OPEN_POSITIONS:
        return False, "maximum bot open positions reached"
    if sum(1 for p in positions if p.symbol == symbol) >= MAX_SYMBOL_POSITIONS:
        return False, "maximum symbol position reached"
    if emergency_stop_active():
        return False, "EMERGENCY STOP ACTIVE (STOP_V73 exists)"
    if daily_loss_pct(account) >= MAX_DAILY_LOSS_PCT:
        return False, f"daily loss limit reached ({daily_loss_pct(account):.2f}%)"

    info = mt5.symbol_info(symbol)
    tick = mt5.symbol_info_tick(symbol)
    if info is None or tick is None:
        return False, "market data unavailable"
    if not info.visible and not mt5.symbol_select(symbol, True):
        return False, "symbol not visible"

    spread_points = (tick.ask - tick.bid) / info.point
    limit = float(SPREAD_LIMITS.get(symbol, 30)) if isinstance(SPREAD_LIMITS, dict) else float(SPREAD_LIMITS)
    if spread_points > limit:
        return False, f"spread {spread_points:.1f} > {limit:.1f} points"

    entry = tick.ask if direction == "BUY" else tick.bid
    atr = float(signal.get("atr", 0))
    if atr <= 0:
        return False, "ATR unavailable"
    distance = ATR_SL_MULT * atr
    if direction == "BUY":
        sl, tp, order_type = entry - distance, entry + RR * distance, mt5.ORDER_TYPE_BUY
    else:
        sl, tp, order_type = entry + distance, entry - RR * distance, mt5.ORDER_TYPE_SELL
    entry, sl, tp = map(lambda x: norm_price(symbol, x), (entry, sl, tp))

    min_stop = float(getattr(info, "trade_stops_level", 0)) * info.point
    freeze = float(getattr(info, "trade_freeze_level", 0)) * info.point
    min_distance = max(min_stop, freeze)
    if min_distance > 0 and abs(entry - sl) < min_distance:
        return False, "SL violates broker stop/freeze distance"
    if min_distance > 0 and abs(tp - entry) < min_distance:
        return False, "TP violates broker stop/freeze distance"

    risk_money = float(account.equity) * RISK_PCT / 100.0
    existing_risk = total_open_risk(positions)
    max_exposure_money = float(account.equity) * MAX_TOTAL_EXPOSURE_PCT / 100.0
    if existing_risk + risk_money > max_exposure_money + 1e-9:
        return False, f"total risk exposure would exceed {MAX_TOTAL_EXPOSURE_PCT:.2f}%"

    volume = calculate_volume(symbol, direction, entry, sl, risk_money)
    if volume is None:
        return False, "calculated volume is below broker minimum or unavailable"

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": entry,
        "sl": sl,
        "tp": tp,
        "deviation": DEVIATION,
        "magic": MAGIC,
        "comment": "DEXORZO-V73",
        "type_time": mt5.ORDER_TIME_GTC,
    }
    result, msg = send_checked_order(request)
    if result is None or getattr(result, "retcode", None) not in {mt5.TRADE_RETCODE_DONE, getattr(mt5, "TRADE_RETCODE_DONE_PARTIAL", -1)}:
        return False, msg

    ticket = getattr(result, "order", 0) or getattr(result, "deal", 0)
    write_trade({
        "timestamp": utc_now().isoformat(), "event": "OPEN", "symbol": symbol,
        "direction": direction, "ticket": ticket, "volume": volume,
        "entry": entry, "sl": sl, "tp": tp, "price": getattr(result, "price", entry),
        "strategies": "|".join(signal.get("strategies", [])), "retcode": result.retcode
    })
    return True, f"OPENED ticket={ticket} volume={volume} entry={getattr(result,'price',entry)}"


def close_position(position, reason="SYSTEM"):
    tick = mt5.symbol_info_tick(position.symbol)
    if tick is None:
        return None, "market tick unavailable"
    if position.type == mt5.POSITION_TYPE_BUY:
        order_type, price = mt5.ORDER_TYPE_SELL, tick.bid
    else:
        order_type, price = mt5.ORDER_TYPE_BUY, tick.ask
    request = {
        "action": mt5.TRADE_ACTION_DEAL, "symbol": position.symbol,
        "volume": position.volume, "type": order_type, "position": position.ticket,
        "price": price, "deviation": DEVIATION, "magic": MAGIC,
        "comment": "DEXORZO-V73-CLOSE", "type_time": mt5.ORDER_TIME_GTC,
    }
    result, msg = send_checked_order(request)
    write_trade({
        "timestamp": utc_now().isoformat(), "event": "CLOSE_REQUEST",
        "symbol": position.symbol, "direction": position_direction(position),
        "ticket": position.ticket, "volume": position.volume, "price": price,
        "profit": position.profit, "r_multiple": position_r_multiple(position),
        "reason": reason, "retcode": getattr(result, "retcode", "") if result else ""
    })
    return result, msg


def metrics(account):
    positions = get_our_positions()
    floating = sum(float(p.profit) for p in positions)
    now = utc_now()
    history = mt5.history_deals_get(datetime(1970, 1, 1, tzinfo=timezone.utc), now)
    realized = 0.0
    wins = losses = 0
    if history:
        for d in history:
            if int(getattr(d, "magic", 0)) == MAGIC and getattr(d, "entry", None) == mt5.DEAL_ENTRY_OUT:
                pnl = float(getattr(d, "profit", 0.0)) + float(getattr(d, "swap", 0.0)) + float(getattr(d, "commission", 0.0))
                realized += pnl
                if pnl > 0: wins += 1
                elif pnl < 0: losses += 1
    return positions, floating, realized, wins, losses


def position_open_datetime(position):
    """Resolve the true opening time from MT5 deal history, with position-time fallback."""
    cache_key = int(getattr(position, "identifier", 0) or getattr(position, "ticket", 0))
    if cache_key in POSITION_OPEN_TIMES:
        return POSITION_OPEN_TIMES[cache_key]

    # Prefer the opening deal timestamp. This avoids relying on a position field
    # that can be unavailable or behave differently across MT5 Python builds.
    try:
        position_id = int(getattr(position, "identifier", 0) or 0)
        if position_id:
            deals = mt5.history_deals_get(position=position_id)
            if deals:
                opening_deals = [
                    d for d in deals
                    if int(getattr(d, "position_id", 0) or 0) == position_id
                    and getattr(d, "entry", None) in (
                        mt5.DEAL_ENTRY_IN,
                        getattr(mt5, "DEAL_ENTRY_INOUT", -999999),
                    )
                ]
                if opening_deals:
                    deal = min(
                        opening_deals,
                        key=lambda d: float(
                            getattr(d, "time_msc", 0)
                            or (getattr(d, "time", 0) * 1000)
                        ),
                    )
                    time_msc = float(
                        getattr(deal, "time_msc", 0)
                        or (getattr(deal, "time", 0) * 1000)
                    )
                    if time_msc > 0:
                        opened = datetime.fromtimestamp(
                            time_msc / 1000.0,
                            tz=timezone.utc,
                        )
                        POSITION_OPEN_TIMES[cache_key] = opened
                        return opened
    except Exception:
        pass

    # Fallback to the position's native open timestamp.
    try:
        time_msc = getattr(position, "time_msc", None)
        if time_msc is not None and float(time_msc) > 0:
            opened = datetime.fromtimestamp(
                float(time_msc) / 1000.0,
                tz=timezone.utc,
            )
        else:
            opened = datetime.fromtimestamp(
                float(position.time),
                tz=timezone.utc,
            )
        POSITION_OPEN_TIMES[cache_key] = opened
        return opened
    except Exception:
        return None


def position_open_epoch(position):
    """Return the MT5 opening timestamp as Unix seconds."""
    opened = position_open_datetime(position)
    if opened is None:
        return None
    try:
        return opened.timestamp()
    except Exception:
        return None


def age_seconds(position):
    opened_epoch = position_open_epoch(position)
    if opened_epoch is None:
        return 0.0

    # Compare Unix timestamps directly. This avoids any timezone/display
    # conversion issues and uses the same epoch basis as MT5 time fields.
    now_epoch = time.time()
    return max(0.0, now_epoch - opened_epoch)


def format_age(position):
    """Display a live, continuously increasing position age."""
    elapsed = age_seconds(position)

    # Never display a newly-opened position as 0s.
    seconds = max(1, int(elapsed))

    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        minutes, secs = divmod(seconds, 60)
        return f"{minutes}m {secs:02d}s"
    if seconds < 86400:
        hours, remainder = divmod(seconds, 3600)
        minutes = remainder // 60
        return f"{hours}h {minutes:02d}m"
    days, remainder = divmod(seconds, 86400)
    hours = remainder // 3600
    return f"{days}d {hours:02d}h"


def fit(text, width):
    return str(text)[:width].ljust(width)


def line(content="", width=82):
    return "|" + fit(content, width - 2) + "|"


def separator(width=82):
    return "+" + "-" * (width - 2) + "+"


def dashboard(account, states, last, error, session_dd):
    # Recover the bot's current positions for the OPEN BOT POSITIONS section.
    positions = get_our_positions()

    # Drop cached open-time entries for positions that no longer exist.
    active_ids = {
        int(getattr(p, "identifier", 0) or getattr(p, "ticket", 0))
        for p in positions
    }
    for cached_id in list(POSITION_OPEN_TIMES):
        if cached_id not in active_ids:
            POSITION_OPEN_TIMES.pop(cached_id, None)

    clear_screen()
    # Re-display the DEXORZO ASCII banner on every dashboard refresh.
    print(DEXORZO_BANNER, end="")

    # Dashboard metrics retained from the original actual content.
    floating = sum(float(p.profit) for p in positions)
    now = utc_now()
    history = mt5.history_deals_get(datetime(1970, 1, 1, tzinfo=timezone.utc), now)
    realized = 0.0
    wins = losses = 0
    if history:
        for d in history:
            if int(getattr(d, "magic", 0)) == MAGIC and getattr(d, "entry", None) == mt5.DEAL_ENTRY_OUT:
                pnl = float(getattr(d, "profit", 0.0)) + float(getattr(d, "swap", 0.0)) + float(getattr(d, "commission", 0.0))
                realized += pnl
                if pnl > 0:
                    wins += 1
                elif pnl < 0:
                    losses += 1

    total = realized + floating
    closed = wins + losses
    wr = wins / closed * 100 if closed else 0.0
    day_realized, _, _, _, _ = daily_stats()
    day_loss = daily_loss_pct(account)
    exposure = total_open_risk(positions)
    max_exposure = float(account.equity) * MAX_TOTAL_EXPOSURE_PCT / 100.0
    stop = "ACTIVE" if emergency_stop_active() else "OFF"

    # Single header box: APP_TITLE and BRAND use exact 40/40 halves.
    print(separator())
    print("|" + fit(APP_TITLE, 40) + fit(BRAND, 40) + "|")
    print(separator())

    # Server heading: centered, dark yellow, same <<< >>> style as OPEN BOT POSITIONS.
    server_heading = f"<<<  Server: {account.server}  >>>".center(80)
    print("|" + YELLOW + server_heading + RESET + "|")
    # One blank boxed line below the connection section.
    print(line())

    # Dashboard metrics use the same 40/40 two-column style throughout.
    print("|" + fit(f"Balance: ${account.balance:,.2f}", 40) + fit(f"Equity: ${account.equity:,.2f}", 40) + "|")
    print("|" + fit(f"Floating P/L: ${floating:,.2f}", 40) + fit(f"Realized P/L: ${realized:,.2f}", 40) + "|")
    # Tracked Profit / Tracked Loss stay visible in the same 40/40 line.
    # Important: pad using the visible text length BEFORE adding ANSI color codes,
    # so the right-hand box border remains exactly aligned.
    profit_amount = f"${total:,.2f}" if total > 0 else "$0.00"
    loss_amount = f"${abs(total):,.2f}" if total < 0 else "$0.00"

    left_label = "Tracked Profit: "
    right_label = "Tracked Loss: "

    left_plain = left_label + profit_amount
    right_plain = right_label + loss_amount

    left_text = (
        GREEN + left_plain + RESET
        if total > 0
        else left_plain
    )
    right_text = (
        right_label + RED + loss_amount + RESET
        if total < 0
        else right_plain
    )

    left_text += " " * max(0, 40 - len(left_plain))
    right_text += " " * max(0, 40 - len(right_plain))

    print("|" + left_text + right_text + "|")
    print("|" + fit(f"Wins / Losses: {wins} / {losses}", 40) + fit(f"Win Rate: {wr:.2f}%", 40) + "|")
    print("|" + fit(f"Open Positions: {len(positions)} / {MAX_OPEN_POSITIONS}", 40) + fit(f"Open Risk: ${exposure:,.2f} / ${max_exposure:,.2f} ({MAX_TOTAL_EXPOSURE_PCT:.2f}%)", 40) + "|")
    print("|" + fit(f"Daily P/L: ${day_realized + floating:,.2f}", 40) + fit(f"Daily Loss: {day_loss:.2f}% / {MAX_DAILY_LOSS_PCT:.2f}%", 40) + "|")
    print("|" + fit(f"Session Drawdown: {session_dd:.2f}%", 40) + fit(f"Emergency STOP: {stop}", 40) + "|")
    print(separator())
    # Symbol status table: 3 symbols on the left and 3 on the right.
    # Each side is exactly 40 characters, so the right column starts at 50%.
    for row in range(3):
        left_symbol = SYMBOLS[row] if row < len(SYMBOLS) else ""
        right_index = row + 3
        right_symbol = SYMBOLS[right_index] if right_index < len(SYMBOLS) else ""

        left_text = (
            f"{left_symbol:<8} {states.get(left_symbol, 'WAITING')}"
            if left_symbol else ""
        )
        right_text = (
            f"{right_symbol:<8} {states.get(right_symbol, 'WAITING')}"
            if right_symbol else ""
        )

        print("|" + fit(left_text, 40) + fit(right_text, 40) + "|")
    print(separator())
    if positions:
        # Same heading style/color as MT5 CONNECTION.
        positions_heading = "<<<  OPEN BOT POSITIONS  >>>".center(80)
        print("|" + YELLOW + positions_heading + RESET + "|")
        # One blank boxed line below the section heading.
        print(line())
        for p in positions:
            direction = position_direction(p)
            tick = mt5.symbol_info_tick(p.symbol)
            current = (tick.bid if direction == "BUY" else tick.ask) if tick else 0.0
            r = position_r_multiple(p)
            dist = abs(current - p.price_open) / (mt5.symbol_info(p.symbol).point or 1) if tick and mt5.symbol_info(p.symbol) else 0.0
            fields = [
                f"{p.symbol} {direction} #{p.ticket}",
                f"Vol {p.volume}",
                f"P/L ${p.profit:.2f}",
                f"R {r:.2f}" if r is not None else "R N/A",
                f"Age {format_age(p)}",
                f"Dist {dist:.0f}pt",
            ]

            # Distribute the available 80-character content width across all fields.
            # This prevents the final Dist value from being clipped by fit().
            total_field_len = sum(len(field) for field in fields)
            gap_count = len(fields) - 1
            available_gap_chars = max(0, 80 - total_field_len)
            if gap_count:
                base_gap, extra_gaps = divmod(available_gap_chars, gap_count)
                gaps = [
                    " " * (base_gap + (1 if i < extra_gaps else 0))
                    for i in range(gap_count)
                ]
            else:
                gaps = []

            position_text = fields[0]
            for i in range(gap_count):
                position_text += gaps[i] + fields[i + 1]

            # Safety: the fields above are designed to fit; do not truncate Dist.
            if len(position_text) < 80:
                position_text += " " * (80 - len(position_text))

            print("|" + position_text + "|")
        print(separator())
    # Split the 80-character dashboard content area into two equal 40-character halves.
    signal_text = f"Last Signal: {last}"
    error_text = f"Last Error: {error}" if error else "Last Error: None"
    half_width = 40
    print("|" + fit(signal_text, half_width) + fit(error_text, half_width) + "|")
    print(separator())
    print("Ctrl+C to stop. Create STOP_V73 in this folder to block NEW entries.")


def main():
    print(DEXORZO_BANNER)
    print(f"{BRAND}")
    print("Starting MT5 AutoTrader V7.3 - Demo only\n")
    connect()
    account = demo_only_guard()
    get_day_start_equity(account)
    current_session_drawdown(float(account.equity))
    print(f"V7.3 safety lock passed: {account.server}")


    engine = SignalEngine(CONFIG)
    states = {s: "WAITING" for s in SYMBOLS}
    seen = {}
    last = "None"
    last_error = ""

    try:
        while True:
            account = demo_only_guard()
            positions = get_our_positions()  # server-side recovery on every cycle
            session_dd = current_session_drawdown(float(account.equity))

            for symbol in SYMBOLS:
                if any(p.symbol == symbol for p in positions):
                    states[symbol] = "DEMO POSITION OPEN"
                else:
                    states[symbol] = "WAITING"

            for symbol in SYMBOLS:
                if any(p.symbol == symbol for p in positions):
                    continue
                try:
                    signal = engine.get_signal(symbol)
                    if not signal:
                        continue
                    signal_time = signal["time"]
                    if not cooldown_ok(symbol, signal_time, seen):
                        states[symbol] = "COOLDOWN"
                        continue
                    seen[symbol] = signal_time
                    ok, msg = send_entry(signal, account, positions)
                    if ok:
                        states[symbol] = f"DEMO {signal['direction']} OPEN"
                        last = f"{symbol} {signal['direction']} | {', '.join(signal.get('strategies', []))}"
                        last_error = ""
                        positions = get_our_positions()
                    else:
                        states[symbol] = "ORDER BLOCKED"
                        last_error = f"{symbol}: {msg}"
                except Exception as exc:
                    states[symbol] = "ERROR"
                    last_error = f"{symbol}: {exc}"

            dashboard(account, states, last, last_error, session_dd)
            time.sleep(SCAN_SECONDS)

    except KeyboardInterrupt:
        print(f"\n{BRAND} - V7.3 stopped by user.")
    finally:
        disconnect()


if __name__ == "__main__":
    main()