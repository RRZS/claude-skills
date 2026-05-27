"""Parse Polymarket weather market questions and outcomes.

The goal is to turn a free-text question + outcome label into a structured
`WeatherMarket`. Anything ambiguous is **dropped** rather than guessed at,
because guessing causes silent bad trades.

Supported question shapes (representative; see tests for the full set):

- Multi-outcome "what will the high be" markets where each outcome label
  carries the bracket, e.g.:
      Q: "Highest temperature in NYC on March 15, 2026?"
      Outcomes: "30 °F or below", "31-32 °F", ..., "57 °F or above"

- Binary "will the high reach X" markets where the question itself carries
  the bracket, e.g.:
      Q: "Will NYC's high temperature on March 15 be 50 °F or above?"
      Outcomes: "Yes", "No"
  Only the YES outcome is emitted; downstream signal logic can produce a
  NO signal symmetrically if needed (v1 logs YES side).
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime, timezone
from typing import Optional

from ..models import BracketKind, TemperatureBracket, WeatherMarket

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# City detection
# ---------------------------------------------------------------------------

# Map of canonical city slug -> regex alternatives. Aliases were chosen to
# match how Polymarket weather markets have historically named locations.
# Expansion path (v2): add Boston, LA, Miami, etc. here AND in
# weather.nws_client.CITY_COORDS.
_CITY_ALIASES: dict[str, list[str]] = {
    "new_york": [
        r"\bnyc\b",
        r"\bnew\s+york(?:\s+city)?\b",
        r"\bmanhattan\b",
        r"\bcentral\s+park\b",
    ],
    "chicago": [
        r"\bchicago\b",
        r"\bo['’]?hare\b",
    ],
}
_CITY_PATTERNS: dict[str, re.Pattern[str]] = {
    slug: re.compile("|".join(aliases), re.IGNORECASE)
    for slug, aliases in _CITY_ALIASES.items()
}


def detect_city(text: str) -> Optional[str]:
    """Return the canonical city slug, or None if no supported city matches."""
    if not text:
        return None
    for slug, pattern in _CITY_PATTERNS.items():
        if pattern.search(text):
            return slug
    return None


# ---------------------------------------------------------------------------
# Weather-shape detection
# ---------------------------------------------------------------------------

# Loose filter: a question that mentions a city but never references
# temperature is probably a non-weather market and we drop it.
_WEATHER_HINT_PATTERN = re.compile(
    r"(°\s*f|\bdegrees\b|\btemperature\b|\bhigh\s+temp|\blow\s+temp|\bthermometer\b)",
    re.IGNORECASE,
)


def looks_like_weather_question(question: str) -> bool:
    return bool(question and _WEATHER_HINT_PATTERN.search(question))


# ---------------------------------------------------------------------------
# Date extraction
# ---------------------------------------------------------------------------

_MONTHS: dict[str, int] = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sept": 9, "sep": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}

_MONTH_NAME_DATE = re.compile(
    r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
    r"aug(?:ust)?|sept?(?:ember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+"
    r"(\d{1,2})(?:st|nd|rd|th)?(?:[,\s]+(\d{4}))?",
    re.IGNORECASE,
)

_NUMERIC_DATE = re.compile(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b")


def extract_target_date(
    text: str,
    *,
    fallback_year: Optional[int] = None,
    today: Optional[date] = None,
) -> Optional[date]:
    """Find a target date in `text`.

    Strategy:
    - Try "Month Day [, Year]" first.
    - Then "M/D[/Y]".
    - If year is missing, use `fallback_year` (e.g. the market close year),
      else the year of `today`. If the resulting date is already in the
      past relative to `today`, roll forward one year — Polymarket weather
      markets only resolve into the future.

    Returns None if no date pattern is found OR if multiple distinct dates
    are found in the same text (ambiguous — we refuse to guess).
    """
    if not text:
        return None
    today = today or datetime.now(timezone.utc).date()

    candidates: list[date] = []

    for m in _MONTH_NAME_DATE.finditer(text):
        month_word = m.group(1).lower()
        day = int(m.group(2))
        year_raw = m.group(3)
        month = _MONTHS.get(month_word)
        if month is None:
            continue
        d = _build_date(month, day, year_raw, fallback_year, today)
        if d is not None:
            candidates.append(d)

    if not candidates:
        for m in _NUMERIC_DATE.finditer(text):
            month = int(m.group(1))
            day = int(m.group(2))
            year_raw = m.group(3)
            d = _build_date(month, day, year_raw, fallback_year, today)
            if d is not None:
                candidates.append(d)

    if not candidates:
        return None

    # If multiple distinct dates appear, we can't tell which one is the
    # target — drop the market.
    unique = list(dict.fromkeys(candidates))
    if len(unique) > 1:
        log.debug("Ambiguous date in text: %s -> %s", text, unique)
        return None
    return unique[0]


def _build_date(
    month: int,
    day: int,
    year_raw: Optional[str],
    fallback_year: Optional[int],
    today: date,
) -> Optional[date]:
    try:
        if year_raw:
            year = int(year_raw)
            if year < 100:
                year += 2000
        elif fallback_year is not None:
            year = fallback_year
        else:
            year = today.year
        d = date(year, month, day)
    except ValueError:
        return None

    # If no explicit year was given and we landed in the past, roll forward.
    if year_raw is None and d < today:
        try:
            d = date(d.year + 1, d.month, d.day)
        except ValueError:
            return None
    return d


# ---------------------------------------------------------------------------
# Bracket extraction
# ---------------------------------------------------------------------------

# Order matters: we try range first, then bounded-from-above/below.
# `_TEMP` allows optional decimals because some markets use half-degree
# brackets. The °F suffix is optional because outcome labels are often
# bare numbers in the same market whose title supplies the °F context.

_TEMP = r"(-?\d+(?:\.\d+)?)"
_F_OPT = r"(?:\s*°\s*F|\s*degrees?\s*F?)?"

_RANGE_DASH = re.compile(
    rf"{_TEMP}\s*[-–—to]+\s*{_TEMP}{_F_OPT}",
    re.IGNORECASE,
)
_RANGE_BETWEEN = re.compile(
    rf"between\s+{_TEMP}{_F_OPT}\s+and\s+{_TEMP}{_F_OPT}",
    re.IGNORECASE,
)
_AT_OR_BELOW = re.compile(
    rf"(?:≤|<=|at\s+most|{_TEMP}{_F_OPT}\s+or\s+(?:below|under|less|lower))",
    re.IGNORECASE,
)
_AT_OR_BELOW_PREFIX = re.compile(
    rf"(?:≤|<=|at\s+most)\s*{_TEMP}{_F_OPT}",
    re.IGNORECASE,
)
_AT_OR_ABOVE = re.compile(
    rf"(?:≥|>=|at\s+least|{_TEMP}{_F_OPT}\s+or\s+(?:above|over|more|higher))",
    re.IGNORECASE,
)
_AT_OR_ABOVE_PREFIX = re.compile(
    rf"(?:≥|>=|at\s+least)\s*{_TEMP}{_F_OPT}",
    re.IGNORECASE,
)
_PLUS_SUFFIX = re.compile(rf"{_TEMP}\s*\+\s*°?\s*F?", re.IGNORECASE)


def extract_bracket(text: str) -> Optional[TemperatureBracket]:
    """Parse a temperature bracket out of a free-text outcome label or question.

    Returns None if no bracket is found. Multiple distinct ranges in the
    same text are treated as ambiguous and rejected.
    """
    if not text:
        return None
    s = text.strip()

    # Range "30-32 °F" / "30 to 32" / "30 - 32"
    range_matches = []
    for m in _RANGE_DASH.finditer(s):
        lo, hi = float(m.group(1)), float(m.group(2))
        if lo <= hi:
            range_matches.append((lo, hi))
    for m in _RANGE_BETWEEN.finditer(s):
        lo, hi = float(m.group(1)), float(m.group(2))
        if lo <= hi:
            range_matches.append((lo, hi))
    if range_matches:
        unique = list(dict.fromkeys(range_matches))
        if len(unique) > 1:
            return None  # ambiguous
        lo, hi = unique[0]
        return TemperatureBracket(kind=BracketKind.RANGE, low_f=lo, high_f=hi)

    # At-or-above with a "+" suffix, e.g. "57+ °F"
    plus_match = _PLUS_SUFFIX.search(s)
    if plus_match:
        return TemperatureBracket(
            kind=BracketKind.AT_OR_ABOVE, low_f=float(plus_match.group(1))
        )

    # Suffix forms: "30 °F or below" / "57 °F or above"
    below_suffix_match = re.search(
        rf"{_TEMP}{_F_OPT}\s+or\s+(?:below|under|less|lower)",
        s,
        re.IGNORECASE,
    )
    if below_suffix_match:
        return TemperatureBracket(
            kind=BracketKind.AT_OR_BELOW, high_f=float(below_suffix_match.group(1))
        )
    above_suffix_match = re.search(
        rf"{_TEMP}{_F_OPT}\s+or\s+(?:above|over|more|higher)",
        s,
        re.IGNORECASE,
    )
    if above_suffix_match:
        return TemperatureBracket(
            kind=BracketKind.AT_OR_ABOVE, low_f=float(above_suffix_match.group(1))
        )

    # Prefix forms: "≤ 30 °F" / ">= 57"
    below_prefix_match = _AT_OR_BELOW_PREFIX.search(s)
    if below_prefix_match:
        return TemperatureBracket(
            kind=BracketKind.AT_OR_BELOW, high_f=float(below_prefix_match.group(1))
        )
    above_prefix_match = _AT_OR_ABOVE_PREFIX.search(s)
    if above_prefix_match:
        return TemperatureBracket(
            kind=BracketKind.AT_OR_ABOVE, low_f=float(above_prefix_match.group(1))
        )

    return None


# ---------------------------------------------------------------------------
# Top-level parse
# ---------------------------------------------------------------------------

def parse_outcome(
    outcome: dict,
    *,
    today: Optional[date] = None,
) -> Optional[WeatherMarket]:
    """Turn one Gamma outcome record into a WeatherMarket, or None on failure.

    Expected input keys (from `gamma_client.GammaClient.iter_outcomes`):
        market_id, condition_id, question, end_date, resolution_source,
        outcome_label, token_id

    Returns None when any required field is missing OR the question /
    outcome doesn't clearly map to a single (city, date, bracket).
    """
    question = (outcome.get("question") or "").strip()
    label = (outcome.get("outcome_label") or "").strip()
    token_id = (outcome.get("token_id") or "").strip()
    market_id = (outcome.get("market_id") or "").strip()
    if not (question and label and token_id and market_id):
        return None

    if not looks_like_weather_question(question):
        return None

    city = detect_city(question)
    if city is None:
        return None

    # Date: prefer date found in the question; if absent, fall back to
    # the market's end date (close time often matches the resolution day).
    close_dt = _parse_iso_datetime(outcome.get("end_date"))
    fallback_year = close_dt.year if close_dt else None
    target_date = extract_target_date(question, fallback_year=fallback_year, today=today)
    if target_date is None:
        return None

    # Bracket: try the outcome label first (multi-outcome case), then the
    # question (binary Yes/No case where the bracket is in the question).
    bracket = extract_bracket(label)
    if bracket is None:
        if label.lower() in {"yes", "yes ", "y"}:
            bracket = extract_bracket(question)
        if bracket is None:
            return None

    return WeatherMarket(
        market_id=market_id,
        token_id=token_id,
        city=city,
        target_date=target_date,
        bracket=bracket,
        outcome_label=label,
        question=question,
        market_close_time=close_dt,
        resolution_source=outcome.get("resolution_source"),
    )


def _parse_iso_datetime(iso_string: Optional[str]) -> Optional[datetime]:
    if not iso_string:
        return None
    # Gamma occasionally returns a trailing "Z" instead of "+00:00".
    cleaned = iso_string.replace("Z", "+00:00") if iso_string.endswith("Z") else iso_string
    try:
        dt = datetime.fromisoformat(cleaned)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
