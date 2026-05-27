"""Risk controls.

These run BEFORE the signal engine (pre-trade sanity) and AFTER the signal
engine (daily caps, deduplication). All real-money safety rules live here.

v1 is paper trading only, but every reject reason here is still tracked
so the same code can gate live trading in v2 without rewrites.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional

from ..config import Config
from ..models import Signal, WeatherMarket

log = logging.getLogger(__name__)


@dataclass
class RiskState:
    """Mutable in-memory counters; reset per UTC day."""

    day: date
    signals_today: int = 0
    seen_token_ids_today: set[str] = field(default_factory=set)


class RiskControls:
    def __init__(self, config: Config) -> None:
        self._cfg = config
        self._state = RiskState(day=_today_utc())

    # ---- pre-signal gating (cheap rejects before forecast/price fetches) ----

    def accept_market_pre_signal(self, market: WeatherMarket) -> Optional[str]:
        """Return None if accepted, else a human-readable rejection reason."""
        if not market.resolution_source:
            return "missing resolution source"

        today = _today_utc()
        horizon_days = (market.target_date - today).days
        if horizon_days < 0:
            return f"target date {market.target_date} is in the past"
        if horizon_days > self._cfg.max_forecast_horizon_days:
            return (
                f"target date {market.target_date} is {horizon_days} days out; "
                f"beyond MAX_FORECAST_HORIZON_DAYS={self._cfg.max_forecast_horizon_days}"
            )

        if market.market_close_time is not None:
            now = datetime.now(timezone.utc)
            if market.market_close_time <= now:
                return "market close time has already passed"

        return None

    # ---- post-signal gating (daily caps, dedupe) ----

    def accept_signal(self, signal: Signal) -> Optional[str]:
        """Return None if accepted, else a rejection reason."""
        self._rollover_day_if_needed()

        if self._state.signals_today >= self._cfg.max_daily_signals:
            return (
                f"daily signal cap reached ({self._state.signals_today}"
                f"/{self._cfg.max_daily_signals})"
            )

        # Deduplicate: don't fire twice on the same token in one day.
        if signal.market.token_id in self._state.seen_token_ids_today:
            return "duplicate signal for this token today"

        # Defensive: position sizing must be > 0 and <= configured cap.
        if signal.position_usd <= 0:
            return "non-positive position size"
        if signal.position_usd > self._cfg.max_position_usd:
            return (
                f"position size {signal.position_usd} > "
                f"MAX_POSITION_USD={self._cfg.max_position_usd}"
            )
        return None

    def record_accepted_signal(self, signal: Signal) -> None:
        """Mark a signal as logged; affects daily counters and dedupe set."""
        self._rollover_day_if_needed()
        self._state.signals_today += 1
        self._state.seen_token_ids_today.add(signal.market.token_id)

    # ---- internals ----

    def _rollover_day_if_needed(self) -> None:
        now_day = _today_utc()
        if now_day != self._state.day:
            log.info(
                "Daily risk state rollover: %s -> %s (was %d signals)",
                self._state.day, now_day, self._state.signals_today,
            )
            self._state = RiskState(day=now_day)


def _today_utc() -> date:
    return datetime.now(timezone.utc).date()
