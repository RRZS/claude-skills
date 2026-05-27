"""Polymarket CLOB public endpoints — prices and order books.

v1 uses ONLY the unauthenticated read endpoints. No signing, no order
submission. The endpoints we touch:

- GET /book?token_id=...     — full order book for a token
- GET /midpoint?token_id=... — midpoint price (when both sides quoted)
- GET /price?token_id=...&side=buy|sell — best bid/ask

We prefer `/book` because a single call yields enough to compute spread
and midpoint without three round trips.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import requests

from ..models import PriceQuote

log = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 10


class ClobPublicClient:
    def __init__(self, base_url: str, session: Optional[requests.Session] = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._session = session or requests.Session()

    def get_book(self, token_id: str) -> Optional[dict[str, Any]]:
        """Return the raw order book payload for a token, or None on error.

        The `/book` payload typically looks like:
            {
              "market": "<condition_id>",
              "asset_id": "<token_id>",
              "bids": [{"price": "0.45", "size": "100"}, ...],
              "asks": [{"price": "0.46", "size": "200"}, ...],
              "timestamp": "...",
              "hash": "..."
            }
        Field names have been stable but the price/size types are strings,
        not floats — be careful when arithmetic'ing.
        """
        url = f"{self._base_url}/book"
        try:
            resp = self._session.get(
                url, params={"token_id": token_id}, timeout=_DEFAULT_TIMEOUT
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            log.debug("CLOB /book failed for %s: %s", token_id, exc)
            return None

    def get_quote(self, token_id: str) -> PriceQuote:
        """Compute a `PriceQuote` for a token from its public order book.

        Returns a PriceQuote with all-None fields if the book is missing
        or empty. Callers should treat that as "unpriced" and skip.
        """
        book = self.get_book(token_id)
        if not book:
            return PriceQuote(token_id=token_id, bid=None, ask=None, yes_price=None, spread=None)

        bids = book.get("bids") or []
        asks = book.get("asks") or []

        # CLOB returns bids sorted high->low and asks low->high, but we
        # don't trust the order — pick best explicitly.
        best_bid = _best_price(bids, want_max=True)
        best_ask = _best_price(asks, want_max=False)

        midpoint: Optional[float]
        spread: Optional[float]
        if best_bid is not None and best_ask is not None:
            midpoint = (best_bid + best_ask) / 2.0
            spread = best_ask - best_bid
        elif best_bid is not None:
            midpoint = best_bid
            spread = None
        elif best_ask is not None:
            midpoint = best_ask
            spread = None
        else:
            midpoint = None
            spread = None

        return PriceQuote(
            token_id=token_id,
            bid=best_bid,
            ask=best_ask,
            yes_price=midpoint,
            spread=spread,
        )


def _best_price(levels: list[dict[str, Any]], *, want_max: bool) -> Optional[float]:
    prices = []
    for lvl in levels:
        raw = lvl.get("price")
        if raw is None:
            continue
        try:
            prices.append(float(raw))
        except (TypeError, ValueError):
            continue
    if not prices:
        return None
    return max(prices) if want_max else min(prices)
