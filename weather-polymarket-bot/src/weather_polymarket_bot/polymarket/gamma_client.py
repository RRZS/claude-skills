"""Polymarket Gamma API client — discovery of active markets.

Gamma is the public, read-only metadata service. No auth, no signing,
just GETs. We use it to list active markets and read their outcomes,
token IDs, close times, and resolution sources.

Endpoint shapes vary over time — see the in-line notes in
`_normalize_market`.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Iterator, Optional

import requests

log = logging.getLogger(__name__)

# Conservative timeout: Gamma is usually fast, but we don't want to hang
# the scan loop on a slow response.
_DEFAULT_TIMEOUT = 15


class GammaClient:
    def __init__(self, base_url: str, session: Optional[requests.Session] = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._session = session or requests.Session()

    def fetch_active_markets(
        self,
        page_limit: int = 500,
        category_hints: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        """Return all active, open markets up to `page_limit`.

        We pull broadly (any active market) rather than filtering on
        category server-side, because Polymarket's category labels for
        weather markets have shifted over time ("Weather", "Climate",
        sometimes none). The downstream parser filters by question text.

        `category_hints` is accepted for future use but ignored in v1.
        """
        params = {
            "active": "true",
            "closed": "false",
            "archived": "false",
            "limit": str(page_limit),
        }
        url = f"{self._base_url}/markets"
        log.debug("GET %s params=%s", url, params)
        resp = self._session.get(url, params=params, timeout=_DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        # Gamma sometimes returns a bare list, sometimes a wrapped object.
        if isinstance(data, dict) and "data" in data:
            raw_markets = data["data"]
        elif isinstance(data, list):
            raw_markets = data
        else:
            log.warning("Unexpected Gamma payload shape: %s", type(data).__name__)
            return []

        normalized = []
        for raw in raw_markets:
            try:
                normalized.append(self._normalize_market(raw))
            except Exception as exc:
                # One malformed market shouldn't kill the scan.
                log.debug("Skipping malformed market: %s", exc)
                continue
        return normalized

    @staticmethod
    def _normalize_market(raw: dict[str, Any]) -> dict[str, Any]:
        """Coerce the raw Gamma payload into a stable shape.

        Polymarket has shipped multiple variants of this response:
        - `outcomes` / `outcomePrices` / `clobTokenIds` are sometimes
          JSON-encoded strings (e.g. '["Yes","No"]') and sometimes
          native arrays.
        - `endDate` field name has appeared as `endDate`, `end_date`,
          `endDateIso`. We try them in order.
        - `resolutionSource` is occasionally absent for very new markets;
          we keep it as None and let risk controls reject.
        """
        outcomes = _maybe_json_list(raw.get("outcomes"))
        outcome_prices = _maybe_json_list(raw.get("outcomePrices"))
        token_ids = _maybe_json_list(raw.get("clobTokenIds"))

        end_date = (
            raw.get("endDate")
            or raw.get("end_date")
            or raw.get("endDateIso")
        )

        return {
            "id": str(raw.get("id") or raw.get("conditionId") or ""),
            "condition_id": raw.get("conditionId"),
            "question": raw.get("question") or raw.get("title") or "",
            "slug": raw.get("slug"),
            "category": raw.get("category"),
            "active": bool(raw.get("active", True)),
            "closed": bool(raw.get("closed", False)),
            "outcomes": outcomes,
            "outcome_prices": outcome_prices,
            "token_ids": token_ids,
            "end_date": end_date,
            "resolution_source": raw.get("resolutionSource") or raw.get("resolution_source"),
            "volume": _maybe_float(raw.get("volume")),
            "raw": raw,
        }

    def iter_outcomes(self, markets: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
        """Flatten markets into one record per outcome.

        Each yielded record is:
            {
                market_id, condition_id, question, end_date, resolution_source,
                outcome_label, outcome_index, token_id, outcome_price,
            }
        Outcomes missing a token_id are skipped — they can't be priced or
        traded.
        """
        for m in markets:
            outcomes = m["outcomes"] or []
            token_ids = m["token_ids"] or []
            prices = m["outcome_prices"] or []
            for i, label in enumerate(outcomes):
                token_id = token_ids[i] if i < len(token_ids) else None
                if not token_id:
                    continue
                outcome_price = None
                if i < len(prices):
                    outcome_price = _maybe_float(prices[i])
                yield {
                    "market_id": m["id"],
                    "condition_id": m["condition_id"],
                    "question": m["question"],
                    "end_date": m["end_date"],
                    "resolution_source": m["resolution_source"],
                    "outcome_label": str(label),
                    "outcome_index": i,
                    "token_id": str(token_id),
                    "outcome_price": outcome_price,
                }


def _maybe_json_list(value: Any) -> list[Any]:
    """Parse a value that might be a JSON string array or already a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (json.JSONDecodeError, ValueError):
            return []
        return parsed if isinstance(parsed, list) else []
    return []


def _maybe_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
