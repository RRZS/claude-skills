"""NOAA / NWS forecast client — daily-high lookup.

The NWS API is free and unauthenticated but REQUIRES a `User-Agent` header
identifying the caller (NOAA blocks empty UAs). It is also a two-step API:

    1. GET /points/{lat},{lon}     -> resolves to a gridpoint
    2. GET /gridpoints/{office}/{gridX},{gridY}/forecast
                                   -> ~7 days of daytime/nighttime periods

We cache the gridpoint per city for the lifetime of the client because it
changes only when NWS resectorizes (very rarely).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Optional

import requests

from ..models import Forecast

log = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 15
_BASE_URL = "https://api.weather.gov"


# Coordinates for supported cities. Lat/lon are NWS-friendly (rounded to 4 dp).
# These match the publicly-known central points used in Polymarket weather
# market resolution (Central Park for NYC, O'Hare-area for Chicago in some
# contracts — but the daily-high forecast does not vary meaningfully at
# city scale, so a single point per city is fine for v1).
CITY_COORDS: dict[str, tuple[float, float]] = {
    "new_york": (40.7128, -74.0060),
    "chicago": (41.8781, -87.6298),
}


@dataclass(frozen=True)
class _Gridpoint:
    office: str
    grid_x: int
    grid_y: int


class NWSClient:
    def __init__(self, user_agent: str, session: Optional[requests.Session] = None) -> None:
        if not user_agent or "example.com" in user_agent.lower():
            log.warning(
                "NWS_USER_AGENT looks like a default/example value. "
                "NOAA expects a real contact in the User-Agent header."
            )
        self._user_agent = user_agent
        self._session = session or requests.Session()
        self._session.headers.update({
            "User-Agent": user_agent,
            "Accept": "application/geo+json",
        })
        self._gridpoint_cache: dict[str, _Gridpoint] = {}

    def get_high_temperature(self, city: str, target_date: date) -> Optional[Forecast]:
        """Return the forecast daily-high in Fahrenheit, or None if unknown.

        Returns None if:
        - the city slug is unsupported,
        - the date is outside the ~7-day forecast window,
        - the NWS API call fails,
        - no daytime period maps onto `target_date`.
        """
        coords = CITY_COORDS.get(city)
        if coords is None:
            log.debug("Unsupported city %r; skipping forecast", city)
            return None

        grid = self._resolve_gridpoint(city, *coords)
        if grid is None:
            return None

        periods = self._fetch_forecast_periods(grid)
        if not periods:
            return None

        high_f = _extract_daytime_high(periods, target_date)
        if high_f is None:
            log.debug("No daytime high for %s on %s in NWS forecast", city, target_date)
            return None

        source = f"NWS api.weather.gov gridpoint {grid.office}/{grid.grid_x},{grid.grid_y}"
        return Forecast(city=city, target_date=target_date, high_f=high_f, source=source)

    def _resolve_gridpoint(self, city: str, lat: float, lon: float) -> Optional[_Gridpoint]:
        cached = self._gridpoint_cache.get(city)
        if cached is not None:
            return cached

        url = f"{_BASE_URL}/points/{lat:.4f},{lon:.4f}"
        try:
            resp = self._session.get(url, timeout=_DEFAULT_TIMEOUT)
            resp.raise_for_status()
            payload = resp.json()
        except requests.RequestException as exc:
            log.warning("NWS /points failed for %s: %s", city, exc)
            return None

        props = payload.get("properties") or {}
        office = props.get("gridId") or props.get("cwa")
        grid_x = props.get("gridX")
        grid_y = props.get("gridY")
        if not office or grid_x is None or grid_y is None:
            log.warning("NWS /points missing gridpoint for %s: %s", city, props)
            return None

        grid = _Gridpoint(office=str(office), grid_x=int(grid_x), grid_y=int(grid_y))
        self._gridpoint_cache[city] = grid
        return grid

    def _fetch_forecast_periods(self, grid: _Gridpoint) -> list[dict[str, Any]]:
        url = f"{_BASE_URL}/gridpoints/{grid.office}/{grid.grid_x},{grid.grid_y}/forecast"
        try:
            resp = self._session.get(url, timeout=_DEFAULT_TIMEOUT)
            resp.raise_for_status()
            payload = resp.json()
        except requests.RequestException as exc:
            log.warning("NWS /forecast failed for %s: %s", grid, exc)
            return []
        return (payload.get("properties") or {}).get("periods") or []


def _extract_daytime_high(periods: list[dict[str, Any]], target_date: date) -> Optional[float]:
    """Find the daytime period covering `target_date` and return its high °F.

    NWS periods alternate daytime/nighttime. `isDaytime=True` periods carry
    the daily high; nighttime carry the low. `temperatureUnit` should be
    "F" for U.S. locations but we convert defensively just in case.
    """
    for period in periods:
        if not period.get("isDaytime"):
            continue
        start_iso = period.get("startTime")
        if not start_iso:
            continue
        period_date = _parse_iso_date(start_iso)
        if period_date != target_date:
            continue
        temp = period.get("temperature")
        unit = (period.get("temperatureUnit") or "F").upper()
        if temp is None:
            return None
        temp_f = float(temp)
        if unit == "C":
            temp_f = temp_f * 9.0 / 5.0 + 32.0
        return temp_f
    return None


def _parse_iso_date(iso_string: str) -> Optional[date]:
    # NWS periods carry timezone-aware ISO strings like
    # "2026-03-15T06:00:00-04:00". `datetime.fromisoformat` handles that
    # natively from Python 3.11+.
    try:
        return datetime.fromisoformat(iso_string).date()
    except ValueError:
        return None
