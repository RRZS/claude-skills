"""Paper trader.

Appends a row per accepted signal to a CSV. No HTTP, no signing, no
network. This is the ONLY "trade execution" surface in v1.

CSV columns (header written on first write):

    timestamp_utc, market_id, token_id, city, target_date,
    bracket_low_f, bracket_high_f, bracket_kind, outcome_label,
    forecast_high_f, market_yes_price, true_probability, edge,
    position_usd, market_close_time, resolution_source

Open the file in append mode each call so concurrent scans (or a crash
mid-run) don't truncate prior history.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path

from ..models import Signal

log = logging.getLogger(__name__)


CSV_COLUMNS = [
    "timestamp_utc",
    "market_id",
    "token_id",
    "city",
    "target_date",
    "bracket_low_f",
    "bracket_high_f",
    "bracket_kind",
    "outcome_label",
    "question",
    "forecast_high_f",
    "market_yes_price",
    "true_probability",
    "edge",
    "position_usd",
    "market_close_time",
    "resolution_source",
]


class PaperTrader:
    def __init__(self, csv_path: Path) -> None:
        self._csv_path = Path(csv_path)
        self._csv_path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, signal: Signal) -> None:
        row = self._signal_to_row(signal)
        write_header = not self._csv_path.exists() or self._csv_path.stat().st_size == 0
        with self._csv_path.open("a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
            if write_header:
                writer.writeheader()
            writer.writerow(row)
        log.info(
            "Paper trade recorded: %s | %s @ %.3f | edge=%.3f | size=$%.2f",
            signal.market.city,
            signal.market.bracket.describe(),
            signal.price.yes_price or 0.0,
            signal.edge,
            signal.position_usd,
        )

    @staticmethod
    def _signal_to_row(signal: Signal) -> dict[str, str]:
        m = signal.market
        b = m.bracket
        return {
            "timestamp_utc": signal.created_at.isoformat(),
            "market_id": m.market_id,
            "token_id": m.token_id,
            "city": m.city,
            "target_date": m.target_date.isoformat(),
            "bracket_low_f": "" if b.low_f is None else f"{b.low_f:g}",
            "bracket_high_f": "" if b.high_f is None else f"{b.high_f:g}",
            "bracket_kind": b.kind.value,
            "outcome_label": m.outcome_label,
            "question": m.question,
            "forecast_high_f": f"{signal.forecast.high_f:g}",
            "market_yes_price": "" if signal.price.yes_price is None else f"{signal.price.yes_price:.4f}",
            "true_probability": f"{signal.true_probability:.4f}",
            "edge": f"{signal.edge:.4f}",
            "position_usd": f"{signal.position_usd:.2f}",
            "market_close_time": "" if m.market_close_time is None else m.market_close_time.isoformat(),
            "resolution_source": m.resolution_source or "",
        }
