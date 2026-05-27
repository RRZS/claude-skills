"""Console notifications.

v1 only prints to stdout; v2 will add Telegram via `notifications/telegram.py`.
Format is intentionally plain-text so it's easy to grep and to forward to
external sinks unchanged.
"""

from __future__ import annotations

from ..models import Signal


def format_signal(signal: Signal) -> str:
    m = signal.market
    p = signal.price
    f = signal.forecast
    yes_price = p.yes_price if p.yes_price is not None else float("nan")
    return (
        f"[SIGNAL] {m.city} {m.target_date} | bracket={m.bracket.describe()} | "
        f"forecast_high={f.high_f:.1f}F | yes_price={yes_price:.3f} | "
        f"true_p={signal.true_probability:.3f} | edge={signal.edge:+.3f} | "
        f"size=${signal.position_usd:.2f} | token={m.token_id[:12]}..."
    )


def print_signal(signal: Signal) -> None:
    print(format_signal(signal), flush=True)


def print_summary(scanned: int, parsed: int, signals: int, rejections: int) -> None:
    print(
        f"[SCAN] scanned={scanned} parsed={parsed} signals={signals} rejected={rejections}",
        flush=True,
    )
