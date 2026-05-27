"""Scanner orchestration.

Top-level loop that wires the modules together:

    Gamma  ->  parser  ->  risk(pre)  ->  NWS forecast  ->  CLOB price
           ->  signal engine          ->  risk(post)    ->  paper trader
                                                       ->  console alert

All I/O failures (network, parsing, forecasts) are caught locally so a
single bad market never kills the scan. The loop maintains a forecast
cache keyed by (city, date) — one scan touches only ~2-3 unique
(city, date) pairs even if the markets list is large.
"""

from __future__ import annotations

import logging
import time
from datetime import date
from typing import Optional

import requests

from .config import Config, load_config
from .models import Forecast, WeatherMarket
from .notifications.console import print_signal, print_summary
from .parsing.market_parser import parse_outcome
from .polymarket.clob_client import ClobPublicClient
from .polymarket.gamma_client import GammaClient
from .risk.risk_controls import RiskControls
from .signals.signal_engine import SignalEngine
from .trading.paper_trader import PaperTrader
from .weather.nws_client import NWSClient

log = logging.getLogger(__name__)


class Scanner:
    def __init__(self, config: Optional[Config] = None) -> None:
        self._cfg = config or load_config()
        self._gamma = GammaClient(self._cfg.gamma_api_base)
        self._clob = ClobPublicClient(self._cfg.clob_api_base)
        self._nws = NWSClient(self._cfg.nws_user_agent)
        self._signals = SignalEngine(self._cfg)
        self._risk = RiskControls(self._cfg)
        self._paper = PaperTrader(self._cfg.paper_trades_csv)

    def run_once(self) -> None:
        """Single scan pass. Safe to call repeatedly."""
        try:
            raw_markets = self._gamma.fetch_active_markets(self._cfg.gamma_page_limit)
        except requests.RequestException as exc:
            log.error("Gamma fetch failed; skipping this scan: %s", exc)
            return

        outcomes = list(self._gamma.iter_outcomes(raw_markets))
        log.info("Gamma returned %d markets / %d priced outcomes", len(raw_markets), len(outcomes))

        forecast_cache: dict[tuple[str, date], Optional[Forecast]] = {}

        scanned = 0
        parsed = 0
        signals_emitted = 0
        rejections = 0

        for outcome in outcomes:
            scanned += 1
            market = parse_outcome(outcome)
            if market is None:
                continue
            if market.city not in self._cfg.cities:
                continue
            parsed += 1

            pre_reject = self._risk.accept_market_pre_signal(market)
            if pre_reject is not None:
                log.debug("Pre-signal reject for %s: %s", market.token_id, pre_reject)
                rejections += 1
                continue

            forecast = self._get_forecast_cached(market, forecast_cache)
            if forecast is None:
                rejections += 1
                continue

            price = self._clob.get_quote(market.token_id)
            if price.yes_price is None:
                rejections += 1
                continue

            signal = self._signals.evaluate(market, forecast, price)
            if signal is None:
                continue

            post_reject = self._risk.accept_signal(signal)
            if post_reject is not None:
                log.info("Post-signal reject for %s: %s", market.token_id, post_reject)
                rejections += 1
                continue

            self._paper.record(signal)
            self._risk.record_accepted_signal(signal)
            print_signal(signal)
            signals_emitted += 1

        print_summary(scanned, parsed, signals_emitted, rejections)

    def run_forever(self) -> None:
        log.info("Starting scan loop; interval=%ss", self._cfg.poll_interval_sec)
        while True:
            try:
                self.run_once()
            except Exception as exc:  # pragma: no cover - defensive top-level
                log.exception("Unhandled error in run_once: %s", exc)
            time.sleep(self._cfg.poll_interval_sec)

    # ---- helpers ----

    def _get_forecast_cached(
        self,
        market: WeatherMarket,
        cache: dict[tuple[str, date], Optional[Forecast]],
    ) -> Optional[Forecast]:
        key = (market.city, market.target_date)
        if key in cache:
            return cache[key]
        forecast = self._nws.get_high_temperature(market.city, market.target_date)
        cache[key] = forecast
        return forecast
