"""Signal engine.

Given:
    - a parsed `WeatherMarket` (city, date, bracket),
    - a NOAA `Forecast` (high_f for that date),
    - a `PriceQuote` from the public CLOB book,

we compute a "true probability" for the bracket using a simple Gaussian
forecast-error model and compare it to the market YES price.

The probability model is deliberately simple in v1:

    temp ~ Normal(forecast_high, sigma)

where `sigma` is configurable (default 2.5 °F). This is a rough match to
short-horizon NWS forecast-error studies but is **not calibrated** to
real historical data. The TODO in README plans the v2 upgrade.

A signal fires when `edge = true_prob - market_yes_price >= MIN_EDGE` AND
all of the price-sanity checks pass (non-degenerate price, tight spread).
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Optional

from ..config import Config
from ..models import (
    BracketKind,
    Forecast,
    PriceQuote,
    Signal,
    TemperatureBracket,
    WeatherMarket,
)

log = logging.getLogger(__name__)


def normal_cdf(x: float) -> float:
    """Standard normal CDF via `math.erf`. No SciPy dependency."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bracket_probability(
    bracket: TemperatureBracket,
    forecast_high_f: float,
    sigma_f: float,
) -> float:
    """P(temp falls in `bracket`) under Normal(forecast_high_f, sigma_f).

    For RANGE [lo, hi]:   Φ((hi - μ)/σ) - Φ((lo - μ)/σ)
    For AT_OR_BELOW hi:   Φ((hi - μ)/σ)
    For AT_OR_ABOVE lo:   1 - Φ((lo - μ)/σ)

    Note: the bracket is treated as inclusive on both ends, and we use the
    raw bracket boundaries without continuity correction. The 0.5 °F
    that would add doesn't materially change the edge calculation.
    """
    if sigma_f <= 0:
        raise ValueError("sigma_f must be positive")

    mu = forecast_high_f
    if bracket.kind is BracketKind.RANGE:
        if bracket.low_f is None or bracket.high_f is None:
            return 0.0
        p_hi = normal_cdf((bracket.high_f - mu) / sigma_f)
        p_lo = normal_cdf((bracket.low_f - mu) / sigma_f)
        return max(0.0, p_hi - p_lo)
    if bracket.kind is BracketKind.AT_OR_BELOW:
        if bracket.high_f is None:
            return 0.0
        return normal_cdf((bracket.high_f - mu) / sigma_f)
    if bracket.kind is BracketKind.AT_OR_ABOVE:
        if bracket.low_f is None:
            return 0.0
        return 1.0 - normal_cdf((bracket.low_f - mu) / sigma_f)
    return 0.0


class SignalEngine:
    def __init__(self, config: Config) -> None:
        self._cfg = config

    def evaluate(
        self,
        market: WeatherMarket,
        forecast: Forecast,
        price: PriceQuote,
    ) -> Optional[Signal]:
        """Return a `Signal` if this trio meets all signal criteria, else None.

        Rejection reasons (logged at DEBUG):
        - forecast city/date mismatch (caller bug),
        - missing market YES price,
        - YES price outside [min_yes_price, max_yes_price],
        - spread above max_spread,
        - edge below MIN_EDGE.
        """
        if market.city != forecast.city or market.target_date != forecast.target_date:
            log.debug("Forecast/market mismatch: %s vs %s", market, forecast)
            return None

        yes_price = price.yes_price
        if yes_price is None:
            log.debug("No YES price for token %s", market.token_id)
            return None
        if yes_price < self._cfg.min_yes_price or yes_price > self._cfg.max_yes_price:
            log.debug(
                "Price %s outside [%s, %s] for %s",
                yes_price, self._cfg.min_yes_price, self._cfg.max_yes_price, market.token_id,
            )
            return None
        if price.spread is not None and price.spread > self._cfg.max_spread:
            log.debug("Spread %.3f > %.3f for %s", price.spread, self._cfg.max_spread, market.token_id)
            return None

        true_prob = bracket_probability(
            market.bracket, forecast.high_f, self._cfg.forecast_temp_stddev_f
        )
        edge = true_prob - yes_price
        if edge < self._cfg.min_edge:
            return None

        return Signal(
            market=market,
            forecast=forecast,
            price=price,
            true_probability=true_prob,
            edge=edge,
            position_usd=self._cfg.max_position_usd,
            created_at=datetime.now(timezone.utc),
        )
