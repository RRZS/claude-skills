"""Tests for `risk.risk_controls`."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from weather_polymarket_bot.config import Config
from weather_polymarket_bot.models import (
    BracketKind,
    Forecast,
    PriceQuote,
    Signal,
    TemperatureBracket,
    WeatherMarket,
)
from weather_polymarket_bot.risk.risk_controls import RiskControls


def _cfg(**over) -> Config:
    defaults = {
        "max_position_usd": 25.0,
        "max_daily_signals": 3,
        "max_forecast_horizon_days": 6,
    }
    defaults.update(over)
    return Config(**defaults)


def _market(**over) -> WeatherMarket:
    base = dict(
        market_id="mkt-1",
        token_id="0xabc",
        city="new_york",
        target_date=date.today() + timedelta(days=1),
        bracket=TemperatureBracket(BracketKind.RANGE, low_f=44, high_f=46),
        outcome_label="44-46 °F",
        question="Highest temperature in NYC tomorrow?",
        market_close_time=datetime.now(timezone.utc) + timedelta(days=1),
        resolution_source="https://www.weather.gov/",
    )
    base.update(over)
    return WeatherMarket(**base)


def _signal(market: WeatherMarket, *, position_usd: float = 25.0) -> Signal:
    return Signal(
        market=market,
        forecast=Forecast(
            city=market.city,
            target_date=market.target_date,
            high_f=45.0,
            source="test",
        ),
        price=PriceQuote(token_id=market.token_id, bid=0.19, ask=0.21, yes_price=0.20, spread=0.02),
        true_probability=0.40,
        edge=0.20,
        position_usd=position_usd,
        created_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Pre-signal checks
# ---------------------------------------------------------------------------

class TestPreSignal:
    def test_accepts_well_formed_market(self) -> None:
        rc = RiskControls(_cfg())
        assert rc.accept_market_pre_signal(_market()) is None

    def test_rejects_missing_resolution_source(self) -> None:
        rc = RiskControls(_cfg())
        reason = rc.accept_market_pre_signal(_market(resolution_source=None))
        assert reason is not None
        assert "resolution source" in reason

    def test_rejects_past_target_date(self) -> None:
        rc = RiskControls(_cfg())
        past = date.today() - timedelta(days=1)
        reason = rc.accept_market_pre_signal(_market(target_date=past))
        assert reason is not None
        assert "past" in reason

    def test_rejects_too_far_in_future(self) -> None:
        rc = RiskControls(_cfg(max_forecast_horizon_days=3))
        far = date.today() + timedelta(days=10)
        reason = rc.accept_market_pre_signal(_market(target_date=far))
        assert reason is not None
        assert "MAX_FORECAST_HORIZON_DAYS" in reason

    def test_rejects_closed_market(self) -> None:
        rc = RiskControls(_cfg())
        past_close = datetime.now(timezone.utc) - timedelta(hours=1)
        reason = rc.accept_market_pre_signal(_market(market_close_time=past_close))
        assert reason is not None
        assert "close time" in reason


# ---------------------------------------------------------------------------
# Post-signal checks
# ---------------------------------------------------------------------------

class TestPostSignal:
    def test_accepts_first_signal(self) -> None:
        rc = RiskControls(_cfg(max_daily_signals=2))
        assert rc.accept_signal(_signal(_market())) is None

    def test_daily_cap_enforced(self) -> None:
        rc = RiskControls(_cfg(max_daily_signals=2))
        s1 = _signal(_market(token_id="t1"))
        s2 = _signal(_market(token_id="t2"))
        s3 = _signal(_market(token_id="t3"))

        assert rc.accept_signal(s1) is None
        rc.record_accepted_signal(s1)
        assert rc.accept_signal(s2) is None
        rc.record_accepted_signal(s2)

        reason = rc.accept_signal(s3)
        assert reason is not None
        assert "daily signal cap" in reason

    def test_dedupes_same_token_same_day(self) -> None:
        rc = RiskControls(_cfg())
        s = _signal(_market(token_id="dup"))
        assert rc.accept_signal(s) is None
        rc.record_accepted_signal(s)
        reason = rc.accept_signal(s)
        assert reason is not None
        assert "duplicate" in reason

    def test_rejects_oversized_position(self) -> None:
        rc = RiskControls(_cfg(max_position_usd=25.0))
        s = _signal(_market(), position_usd=100.0)
        reason = rc.accept_signal(s)
        assert reason is not None
        assert "position size" in reason

    def test_rejects_non_positive_position(self) -> None:
        rc = RiskControls(_cfg())
        s = _signal(_market(), position_usd=0.0)
        reason = rc.accept_signal(s)
        assert reason is not None
        assert "non-positive" in reason
