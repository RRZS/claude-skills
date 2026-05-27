"""Environment-driven configuration.

Loads from `.env` if present (via python-dotenv), then OS env. All values
have safe defaults so the bot can run with an unedited `.env.example`
copied to `.env`, except `NWS_USER_AGENT` which NOAA requires.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv is optional at runtime; tests don't need it.
    pass


def _env_str(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _env_float(key: str, default: float) -> float:
    raw = os.environ.get(key)
    if raw is None or raw == "":
        return default
    return float(raw)


def _env_int(key: str, default: int) -> int:
    raw = os.environ.get(key)
    if raw is None or raw == "":
        return default
    return int(raw)


def _env_list(key: str, default: list[str]) -> list[str]:
    raw = os.environ.get(key)
    if raw is None or raw == "":
        return list(default)
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Config:
    # NOAA / NWS
    nws_user_agent: str = field(
        default_factory=lambda: _env_str(
            "NWS_USER_AGENT",
            "weather-polymarket-bot (contact@example.com)",
        )
    )

    # Polymarket public endpoints
    gamma_api_base: str = field(
        default_factory=lambda: _env_str("GAMMA_API_BASE", "https://gamma-api.polymarket.com")
    )
    clob_api_base: str = field(
        default_factory=lambda: _env_str("CLOB_API_BASE", "https://clob.polymarket.com")
    )

    # Scanner
    cities: list[str] = field(
        default_factory=lambda: _env_list("CITIES", ["new_york", "chicago"])
    )
    poll_interval_sec: int = field(default_factory=lambda: _env_int("POLL_INTERVAL_SEC", 300))
    gamma_page_limit: int = field(default_factory=lambda: _env_int("GAMMA_PAGE_LIMIT", 500))

    # Signal engine
    min_edge: float = field(default_factory=lambda: _env_float("MIN_EDGE", 0.05))
    forecast_temp_stddev_f: float = field(
        default_factory=lambda: _env_float("FORECAST_TEMP_STDDEV_F", 2.5)
    )
    max_spread: float = field(default_factory=lambda: _env_float("MAX_SPREAD", 0.05))
    min_yes_price: float = field(default_factory=lambda: _env_float("MIN_YES_PRICE", 0.02))
    max_yes_price: float = field(default_factory=lambda: _env_float("MAX_YES_PRICE", 0.98))

    # Risk controls
    max_position_usd: float = field(default_factory=lambda: _env_float("MAX_POSITION_USD", 25.0))
    max_daily_signals: int = field(default_factory=lambda: _env_int("MAX_DAILY_SIGNALS", 20))
    max_forecast_horizon_days: int = field(
        default_factory=lambda: _env_int("MAX_FORECAST_HORIZON_DAYS", 6)
    )

    # Output
    paper_trades_csv: Path = field(
        default_factory=lambda: Path(_env_str("PAPER_TRADES_CSV", "logs/paper_trades.csv"))
    )
    log_level: str = field(default_factory=lambda: _env_str("LOG_LEVEL", "INFO"))


def load_config() -> Config:
    """Build a Config from the current environment.

    Safe to call multiple times. python-dotenv already ran at import time,
    so OS env is the source of truth here.
    """
    return Config()
