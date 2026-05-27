"""Tests for `parsing.market_parser`.

Covers the public surface: detect_city, looks_like_weather_question,
extract_target_date, extract_bracket, parse_outcome.

All test data is hand-crafted from real-shape Polymarket weather market
titles. The parser is intentionally strict: anything ambiguous returns
None.
"""

from __future__ import annotations

from datetime import date

import pytest

from weather_polymarket_bot.models import BracketKind
from weather_polymarket_bot.parsing.market_parser import (
    detect_city,
    extract_bracket,
    extract_target_date,
    looks_like_weather_question,
    parse_outcome,
)


# ---------------------------------------------------------------------------
# detect_city
# ---------------------------------------------------------------------------

class TestDetectCity:
    @pytest.mark.parametrize("text,expected", [
        ("Highest temperature in NYC on March 15?", "new_york"),
        ("What will the high in New York be?", "new_york"),
        ("New York City weather high March 15", "new_york"),
        ("Manhattan high temperature March 15", "new_york"),
        ("Central Park high March 15", "new_york"),
        ("Chicago high temperature March 15", "chicago"),
        ("O'Hare high temperature March 15", "chicago"),
        ("o'hare temp", "chicago"),
    ])
    def test_known_cities(self, text: str, expected: str) -> None:
        assert detect_city(text) == expected

    @pytest.mark.parametrize("text", [
        "Boston high temperature March 15",
        "Miami weather",
        "",
        "no city here",
        "Will the Yankees win?",
    ])
    def test_unsupported_or_missing(self, text: str) -> None:
        assert detect_city(text) is None


# ---------------------------------------------------------------------------
# looks_like_weather_question
# ---------------------------------------------------------------------------

class TestLooksLikeWeather:
    @pytest.mark.parametrize("text", [
        "Highest temperature in NYC on March 15?",
        "Will NYC reach 50°F on March 15?",
        "Chicago high temp March 15",
        "What will the high temperature be?",
        "50 degrees F",
    ])
    def test_positive(self, text: str) -> None:
        assert looks_like_weather_question(text) is True

    @pytest.mark.parametrize("text", [
        "Will the Yankees win the World Series?",
        "Bitcoin price March 15",
        "",
        "NYC mayoral election",
    ])
    def test_negative(self, text: str) -> None:
        assert looks_like_weather_question(text) is False


# ---------------------------------------------------------------------------
# extract_target_date
# ---------------------------------------------------------------------------

class TestExtractTargetDate:
    TODAY = date(2026, 3, 1)

    def test_month_name_with_year(self) -> None:
        d = extract_target_date("high on March 15, 2026", today=self.TODAY)
        assert d == date(2026, 3, 15)

    def test_month_name_without_year_future(self) -> None:
        d = extract_target_date("high on March 15", today=self.TODAY)
        assert d == date(2026, 3, 15)

    def test_month_name_without_year_rolls_forward(self) -> None:
        # Feb 1 is in the past for today=2026-03-01; should roll to 2027.
        d = extract_target_date("high on February 1", today=self.TODAY)
        assert d == date(2027, 2, 1)

    def test_uses_fallback_year(self) -> None:
        d = extract_target_date("high on March 15", fallback_year=2027, today=self.TODAY)
        assert d == date(2027, 3, 15)

    def test_short_month(self) -> None:
        d = extract_target_date("Mar 15, 2026", today=self.TODAY)
        assert d == date(2026, 3, 15)

    def test_ordinal_suffix(self) -> None:
        d = extract_target_date("March 15th, 2026", today=self.TODAY)
        assert d == date(2026, 3, 15)

    def test_numeric_date(self) -> None:
        d = extract_target_date("high on 3/15/2026", today=self.TODAY)
        assert d == date(2026, 3, 15)

    def test_no_date(self) -> None:
        assert extract_target_date("no date here at all", today=self.TODAY) is None

    def test_two_distinct_dates_is_ambiguous(self) -> None:
        d = extract_target_date(
            "high between March 15 and March 16, 2026",
            today=self.TODAY,
        )
        assert d is None

    def test_same_date_twice_is_fine(self) -> None:
        # Same canonical date is not ambiguous.
        d = extract_target_date(
            "March 15, 2026 (specifically March 15, 2026)",
            today=self.TODAY,
        )
        assert d == date(2026, 3, 15)

    def test_invalid_date_returns_none(self) -> None:
        assert extract_target_date("Feb 30, 2026", today=self.TODAY) is None


# ---------------------------------------------------------------------------
# extract_bracket
# ---------------------------------------------------------------------------

class TestExtractBracket:
    def test_range_dash(self) -> None:
        b = extract_bracket("31-32 °F")
        assert b is not None
        assert b.kind is BracketKind.RANGE
        assert b.low_f == 31 and b.high_f == 32

    def test_range_dash_no_unit(self) -> None:
        b = extract_bracket("31-32")
        assert b is not None
        assert b.kind is BracketKind.RANGE
        assert (b.low_f, b.high_f) == (31, 32)

    def test_range_endash(self) -> None:
        b = extract_bracket("31–32 °F")
        assert b is not None
        assert b.kind is BracketKind.RANGE
        assert (b.low_f, b.high_f) == (31, 32)

    def test_range_to(self) -> None:
        b = extract_bracket("31 to 32 °F")
        assert b is not None
        assert b.kind is BracketKind.RANGE
        assert (b.low_f, b.high_f) == (31, 32)

    def test_range_between(self) -> None:
        b = extract_bracket("between 30 and 35 °F")
        assert b is not None
        assert b.kind is BracketKind.RANGE
        assert (b.low_f, b.high_f) == (30, 35)

    def test_at_or_below_suffix(self) -> None:
        b = extract_bracket("30 °F or below")
        assert b is not None
        assert b.kind is BracketKind.AT_OR_BELOW
        assert b.high_f == 30

    def test_at_or_below_unicode(self) -> None:
        b = extract_bracket("≤ 30 °F")
        assert b is not None
        assert b.kind is BracketKind.AT_OR_BELOW
        assert b.high_f == 30

    def test_at_or_below_prefix(self) -> None:
        b = extract_bracket("<= 30 °F")
        assert b is not None
        assert b.kind is BracketKind.AT_OR_BELOW
        assert b.high_f == 30

    def test_at_or_above_suffix(self) -> None:
        b = extract_bracket("57 °F or above")
        assert b is not None
        assert b.kind is BracketKind.AT_OR_ABOVE
        assert b.low_f == 57

    def test_at_or_above_plus(self) -> None:
        b = extract_bracket("57+ °F")
        assert b is not None
        assert b.kind is BracketKind.AT_OR_ABOVE
        assert b.low_f == 57

    def test_at_or_above_unicode(self) -> None:
        b = extract_bracket("≥ 57 °F")
        assert b is not None
        assert b.kind is BracketKind.AT_OR_ABOVE
        assert b.low_f == 57

    def test_empty_returns_none(self) -> None:
        assert extract_bracket("") is None

    def test_unparseable_label(self) -> None:
        assert extract_bracket("Yes") is None

    def test_bracket_contains(self) -> None:
        b = extract_bracket("31-32 °F")
        assert b is not None
        assert b.contains(31) is True
        assert b.contains(32) is True
        assert b.contains(31.5) is True
        assert b.contains(30) is False
        assert b.contains(33) is False


# ---------------------------------------------------------------------------
# parse_outcome
# ---------------------------------------------------------------------------

class TestParseOutcome:
    TODAY = date(2026, 3, 1)

    def _make_outcome(self, **overrides) -> dict:
        base = {
            "market_id": "mkt-123",
            "condition_id": "cond-xyz",
            "question": "Highest temperature in NYC on March 15, 2026?",
            "end_date": "2026-03-15T23:59:59Z",
            "resolution_source": "https://www.weather.gov/",
            "outcome_label": "31-32 °F",
            "token_id": "0xabc",
        }
        base.update(overrides)
        return base

    def test_multi_outcome_range(self) -> None:
        wm = parse_outcome(self._make_outcome(), today=self.TODAY)
        assert wm is not None
        assert wm.city == "new_york"
        assert wm.target_date == date(2026, 3, 15)
        assert wm.bracket.kind is BracketKind.RANGE
        assert wm.bracket.low_f == 31 and wm.bracket.high_f == 32
        assert wm.token_id == "0xabc"
        assert wm.market_close_time is not None

    def test_multi_outcome_at_or_below(self) -> None:
        wm = parse_outcome(
            self._make_outcome(outcome_label="30 °F or below"),
            today=self.TODAY,
        )
        assert wm is not None
        assert wm.bracket.kind is BracketKind.AT_OR_BELOW
        assert wm.bracket.high_f == 30

    def test_multi_outcome_at_or_above(self) -> None:
        wm = parse_outcome(
            self._make_outcome(outcome_label="57+ °F"),
            today=self.TODAY,
        )
        assert wm is not None
        assert wm.bracket.kind is BracketKind.AT_OR_ABOVE
        assert wm.bracket.low_f == 57

    def test_binary_yes_parses_question_bracket(self) -> None:
        wm = parse_outcome(
            self._make_outcome(
                question="Will NYC's high temperature on March 15, 2026 be 50 °F or above?",
                outcome_label="Yes",
            ),
            today=self.TODAY,
        )
        assert wm is not None
        assert wm.bracket.kind is BracketKind.AT_OR_ABOVE
        assert wm.bracket.low_f == 50

    def test_chicago_with_numeric_date(self) -> None:
        wm = parse_outcome(
            self._make_outcome(
                question="Chicago high temperature on 3/15/2026?",
                outcome_label="40-45 °F",
            ),
            today=self.TODAY,
        )
        assert wm is not None
        assert wm.city == "chicago"
        assert wm.target_date == date(2026, 3, 15)

    def test_rejects_unsupported_city(self) -> None:
        wm = parse_outcome(
            self._make_outcome(question="Boston high temperature March 15, 2026?"),
            today=self.TODAY,
        )
        assert wm is None

    def test_rejects_non_weather_question(self) -> None:
        wm = parse_outcome(
            self._make_outcome(question="Will NYC's mayor be re-elected on March 15, 2026?"),
            today=self.TODAY,
        )
        assert wm is None

    def test_rejects_missing_token_id(self) -> None:
        wm = parse_outcome(self._make_outcome(token_id=""), today=self.TODAY)
        assert wm is None

    def test_rejects_missing_question(self) -> None:
        wm = parse_outcome(self._make_outcome(question=""), today=self.TODAY)
        assert wm is None

    def test_rejects_no_bracket(self) -> None:
        # Outcome label has no bracket and is not "Yes" -> drop.
        wm = parse_outcome(
            self._make_outcome(outcome_label="Maybe"),
            today=self.TODAY,
        )
        assert wm is None

    def test_rejects_ambiguous_date(self) -> None:
        wm = parse_outcome(
            self._make_outcome(
                question="NYC high temperature on March 15 or March 16, 2026?"
            ),
            today=self.TODAY,
        )
        assert wm is None

    def test_no_outcome_when_no_date_at_all(self) -> None:
        wm = parse_outcome(
            self._make_outcome(
                question="NYC high temperature?",
                end_date=None,
            ),
            today=self.TODAY,
        )
        assert wm is None

    def test_no_recreated_when_no_resolution_source(self) -> None:
        # parse_outcome itself does NOT reject on missing resolution source —
        # that's the risk-controls layer. Parser should still succeed.
        wm = parse_outcome(
            self._make_outcome(resolution_source=None),
            today=self.TODAY,
        )
        assert wm is not None
        assert wm.resolution_source is None
