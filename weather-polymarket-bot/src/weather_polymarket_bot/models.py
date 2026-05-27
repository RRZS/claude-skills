"""Shared dataclasses used across the bot."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional


class BracketKind(str, Enum):
    """Shape of a temperature bracket on a Polymarket weather outcome."""

    RANGE = "range"             # e.g. 30-32 F
    AT_OR_BELOW = "at_or_below" # e.g. "30 F or below"
    AT_OR_ABOVE = "at_or_above" # e.g. "57 F or above"


@dataclass(frozen=True)
class TemperatureBracket:
    """A single temperature outcome on a market.

    For RANGE: both `low_f` and `high_f` are set and inclusive.
    For AT_OR_BELOW: only `high_f` is meaningful (the upper bound, inclusive).
    For AT_OR_ABOVE: only `low_f` is meaningful (the lower bound, inclusive).
    """

    kind: BracketKind
    low_f: Optional[float] = None
    high_f: Optional[float] = None

    def contains(self, temp_f: float) -> bool:
        if self.kind is BracketKind.RANGE:
            return self.low_f is not None and self.high_f is not None \
                and self.low_f <= temp_f <= self.high_f
        if self.kind is BracketKind.AT_OR_BELOW:
            return self.high_f is not None and temp_f <= self.high_f
        if self.kind is BracketKind.AT_OR_ABOVE:
            return self.low_f is not None and temp_f >= self.low_f
        return False

    def describe(self) -> str:
        if self.kind is BracketKind.RANGE:
            return f"{self.low_f:g}-{self.high_f:g} F"
        if self.kind is BracketKind.AT_OR_BELOW:
            return f"<= {self.high_f:g} F"
        if self.kind is BracketKind.AT_OR_ABOVE:
            return f">= {self.low_f:g} F"
        return "unknown"


@dataclass(frozen=True)
class WeatherMarket:
    """A parsed Polymarket weather outcome ready for evaluation.

    A "market" in Polymarket terminology may have multiple outcomes; we
    flatten each outcome into its own WeatherMarket for simpler downstream
    handling. `market_id` will repeat across siblings; `token_id` is unique.
    """

    market_id: str
    token_id: str
    city: str
    target_date: date
    bracket: TemperatureBracket
    outcome_label: str
    question: str
    market_close_time: Optional[datetime]
    resolution_source: Optional[str]


@dataclass(frozen=True)
class PriceQuote:
    """Snapshot of the public CLOB book for a token.

    `yes_price` is the midpoint when both sides are quoted, else the
    single-sided last available. `spread` is `ask - bid`; `None` if
    one side is missing.
    """

    token_id: str
    bid: Optional[float]
    ask: Optional[float]
    yes_price: Optional[float]
    spread: Optional[float]


@dataclass(frozen=True)
class Forecast:
    """A single daily-high forecast from NWS."""

    city: str
    target_date: date
    high_f: float
    source: str  # e.g. "NWS api.weather.gov gridpoint <office>/<x>,<y>"


@dataclass(frozen=True)
class Signal:
    """A paper-trade signal ready for CSV logging.

    Carries both the source observations (forecast, price) and the derived
    quantities (true_probability, edge, position_usd) so the CSV row can be
    rebuilt without joining files later.
    """

    market: WeatherMarket
    forecast: Forecast
    price: PriceQuote
    true_probability: float
    edge: float
    position_usd: float
    created_at: datetime
