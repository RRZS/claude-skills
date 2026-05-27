"""Tests for `signals.signal_engine`.

Covers:
- `bracket_probability` math for all three bracket kinds.
- `SignalEngine.evaluate` accept/reject paths.
"""

from __future__ import annotations

import math
from datetime import date, datetime, timezone

import pytest

from weather_polymarket_bot.config import Config
from weather_polymarket_bot.models import (
    BracketKind,
    Forecast,
    PriceQuote,
    TemperatureBracket,
    WeatherMarket,
)
from weather_polymarket_bot.signals.signal_engine import (
    SignalEngine,
    bracket_probability,
    normal_cdf,
)


# ---------------------------------------------------------------------------
# normal_cdf — spot checks
# ---------------------------------------------------------------------------

class TestNormalCdf:
    def test_zero(self) -> None:
        assert math.isclose(normal_cdf(0.0), 0.5, abs_tol=1e-6)

    def test_symmetry(self) -> None:
        for x in (0.5, 1.0, 2.5, 3.0):
            assert math.isclose(normal_cdf(x) + normal_cdf(-x), 1.0, abs_tol=1e-9)

    def test_known_values(self) -> None:
        # Standard textbook approximations
        assert math.isclose(normal_cdf(1.0), 0.8413, abs_tol=1e-3)
        assert math.isclose(normal_cdf(1.96), 0.975, abs_tol=1e-3)


# ---------------------------------------------------------------------------
# bracket_probability
# ---------------------------------------------------------------------------

class TestBracketProbability:
    def test_range_centered_on_forecast(self) -> None:
        # forecast=45, bracket [44, 46] is symmetric around forecast.
        # With sigma=1, this should be Φ(1) - Φ(-1) ≈ 0.6827.
        b = TemperatureBracket(BracketKind.RANGE, low_f=44, high_f=46)
        p = bracket_probability(b, forecast_high_f=45, sigma_f=1.0)
        assert math.isclose(p, 0.6827, abs_tol=1e-3)

    def test_range_far_from_forecast_is_tiny(self) -> None:
        b = TemperatureBracket(BracketKind.RANGE, low_f=80, high_f=82)
        p = bracket_probability(b, forecast_high_f=45, sigma_f=2.5)
        assert p < 1e-10

    def test_at_or_below_at_forecast_is_half(self) -> None:
        b = TemperatureBracket(BracketKind.AT_OR_BELOW, high_f=45)
        p = bracket_probability(b, forecast_high_f=45, sigma_f=2.5)
        assert math.isclose(p, 0.5, abs_tol=1e-6)

    def test_at_or_above_at_forecast_is_half(self) -> None:
        b = TemperatureBracket(BracketKind.AT_OR_ABOVE, low_f=45)
        p = bracket_probability(b, forecast_high_f=45, sigma_f=2.5)
        assert math.isclose(p, 0.5, abs_tol=1e-6)

    def test_at_or_below_well_above_forecast_is_near_one(self) -> None:
        b = TemperatureBracket(BracketKind.AT_OR_BELOW, high_f=80)
        p = bracket_probability(b, forecast_high_f=45, sigma_f=2.5)
        assert p > 0.9999

    def test_at_or_above_well_above_forecast_is_near_zero(self) -> None:
        b = TemperatureBracket(BracketKind.AT_OR_ABOVE, low_f=80)
        p = bracket_probability(b, forecast_high_f=45, sigma_f=2.5)
        assert p < 1e-4

    def test_range_with_missing_bounds_is_zero(self) -> None:
        b = TemperatureBracket(BracketKind.RANGE, low_f=None, high_f=None)
        assert bracket_probability(b, 45, 2.5) == 0.0

    def test_zero_sigma_raises(self) -> None:
        b = TemperatureBracket(BracketKind.RANGE, low_f=30, high_f=32)
        with pytest.raises(ValueError):
            bracket_probability(b, 45, 0.0)

    def test_three_brackets_partition_probability(self) -> None:
        # AT_OR_BELOW(40) + RANGE(41, 50) + AT_OR_ABOVE(51) should sum to ~1.
        # (Not exactly 1 because the bracket boundaries are inclusive on both
        # ends, but with continuous Normal the integer-step gap is zero.)
        b1 = TemperatureBracket(BracketKind.AT_OR_BELOW, high_f=40)
        b2 = TemperatureBracket(BracketKind.RANGE, low_f=40, high_f=51)
        b3 = TemperatureBracket(BracketKind.AT_OR_ABOVE, low_f=51)
        total = (
            bracket_probability(b1, 45, 2.5)
            + bracket_probability(b2, 45, 2.5)
            + bracket_probability(b3, 45, 2.5)
        )
        assert math.isclose(total, 1.0, abs_tol=1e-6)


# ---------------------------------------------------------------------------
# SignalEngine.evaluate
# ---------------------------------------------------------------------------

class TestEvaluate:
    def _cfg(self, **over) -> Config:
        defaults = {
            "min_edge": 0.05,
            "forecast_temp_stddev_f": 2.5,
            "max_spread": 0.05,
            "min_yes_price": 0.02,
            "max_yes_price": 0.98,
            "max_position_usd": 25.0,
        }
        defaults.update(over)
        # Build a Config via constructor with the overrides. Other fields
        # take their dataclass defaults from env.
        return Config(**defaults)

    def _market(self, bracket: TemperatureBracket) -> WeatherMarket:
        return WeatherMarket(
            market_id="mkt-1",
            token_id="0xabc",
            city="new_york",
            target_date=date(2026, 3, 15),
            bracket=bracket,
            outcome_label="44-46 °F",
            question="Highest temperature in NYC on March 15, 2026?",
            market_close_time=datetime(2026, 3, 15, 23, 59, tzinfo=timezone.utc),
            resolution_source="https://www.weather.gov/",
        )

    def _forecast(self) -> Forecast:
        return Forecast(
            city="new_york",
            target_date=date(2026, 3, 15),
            high_f=45.0,
            source="test",
        )

    def _quote(self, *, yes_price: float | None, spread: float | None = 0.02) -> PriceQuote:
        bid = (yes_price - spread / 2) if (yes_price is not None and spread is not None) else None
        ask = (yes_price + spread / 2) if (yes_price is not None and spread is not None) else None
        return PriceQuote(token_id="0xabc", bid=bid, ask=ask, yes_price=yes_price, spread=spread)

    def test_fires_when_true_prob_exceeds_market_price(self) -> None:
        engine = SignalEngine(self._cfg())
        market = self._market(TemperatureBracket(BracketKind.RANGE, low_f=44, high_f=46))
        sig = engine.evaluate(market, self._forecast(), self._quote(yes_price=0.20))
        assert sig is not None
        # true_prob ~ 0.31 (Φ(0.4)-Φ(-0.4) with sigma=2.5). Edge ≈ 0.11.
        assert sig.true_probability > 0.30
        assert sig.edge > 0.05
        assert sig.position_usd == 25.0

    def test_no_signal_when_edge_below_threshold(self) -> None:
        engine = SignalEngine(self._cfg())
        market = self._market(TemperatureBracket(BracketKind.RANGE, low_f=44, high_f=46))
        sig = engine.evaluate(market, self._forecast(), self._quote(yes_price=0.30))
        assert sig is None

    def test_no_signal_when_yes_price_missing(self) -> None:
        engine = SignalEngine(self._cfg())
        market = self._market(TemperatureBracket(BracketKind.RANGE, low_f=44, high_f=46))
        sig = engine.evaluate(market, self._forecast(), self._quote(yes_price=None, spread=None))
        assert sig is None

    def test_no_signal_when_spread_too_wide(self) -> None:
        engine = SignalEngine(self._cfg(max_spread=0.05))
        market = self._market(TemperatureBracket(BracketKind.RANGE, low_f=44, high_f=46))
        sig = engine.evaluate(market, self._forecast(), self._quote(yes_price=0.20, spread=0.20))
        assert sig is None

    def test_no_signal_when_price_below_min(self) -> None:
        engine = SignalEngine(self._cfg())
        market = self._market(TemperatureBracket(BracketKind.RANGE, low_f=44, high_f=46))
        sig = engine.evaluate(market, self._forecast(), self._quote(yes_price=0.01))
        assert sig is None

    def test_no_signal_when_price_above_max(self) -> None:
        engine = SignalEngine(self._cfg())
        market = self._market(TemperatureBracket(BracketKind.RANGE, low_f=44, high_f=46))
        sig = engine.evaluate(market, self._forecast(), self._quote(yes_price=0.995))
        assert sig is None

    def test_no_signal_when_city_mismatch(self) -> None:
        engine = SignalEngine(self._cfg())
        market = self._market(TemperatureBracket(BracketKind.RANGE, low_f=44, high_f=46))
        bad_forecast = Forecast(
            city="chicago",
            target_date=date(2026, 3, 15),
            high_f=45.0,
            source="test",
        )
        sig = engine.evaluate(market, bad_forecast, self._quote(yes_price=0.20))
        assert sig is None

    def test_no_signal_when_date_mismatch(self) -> None:
        engine = SignalEngine(self._cfg())
        market = self._market(TemperatureBracket(BracketKind.RANGE, low_f=44, high_f=46))
        bad_forecast = Forecast(
            city="new_york",
            target_date=date(2026, 3, 16),
            high_f=45.0,
            source="test",
        )
        sig = engine.evaluate(market, bad_forecast, self._quote(yes_price=0.20))
        assert sig is None

    def test_fires_on_at_or_below_when_forecast_well_below(self) -> None:
        # Forecast 45, bracket "<= 60" should have true_prob ~ 1.0.
        engine = SignalEngine(self._cfg())
        market = self._market(TemperatureBracket(BracketKind.AT_OR_BELOW, high_f=60))
        sig = engine.evaluate(market, self._forecast(), self._quote(yes_price=0.50))
        assert sig is not None
        assert sig.true_probability > 0.99
        assert sig.edge > 0.4
