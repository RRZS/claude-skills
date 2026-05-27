"""Parser-coverage diagnostic for the live Polymarket Gamma API.

Run this when you want to know: "How many of the active markets right now
does my parser handle, and where are the rest dropping?"

It hits ONLY the public Gamma endpoint. No CLOB, no NWS, no auth. It does
not place trades and it does not write to `logs/paper_trades.csv` — the
output is purely diagnostic.

Usage:

    cd weather-polymarket-bot
    pip install -r requirements.txt
    PYTHONPATH=src python scripts/parser_coverage.py
    PYTHONPATH=src python scripts/parser_coverage.py --json drops.json

Output sections:

    1. Stage counts        — how many markets survive each filter
    2. City+weather sample — what we matched on the city/temperature filter
    3. Drop reasons        — which parser stage rejected each unmatched outcome

If you see lots of `weather_but_unparsed` with a single dominant reason
(e.g. "no_bracket"), that's a parser gap worth fixing. Paste the printed
samples in the issue / PR so the regex can be extended.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

# Allow running as `python scripts/parser_coverage.py` from project root
# without PYTHONPATH gymnastics.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from weather_polymarket_bot.config import load_config  # noqa: E402
from weather_polymarket_bot.parsing.market_parser import (  # noqa: E402
    detect_city,
    extract_bracket,
    extract_target_date,
    looks_like_weather_question,
    parse_outcome,
)
from weather_polymarket_bot.polymarket.gamma_client import GammaClient  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--json",
        type=Path,
        default=None,
        help="Optional path to dump full drop diagnostics as JSON.",
    )
    ap.add_argument(
        "--samples",
        type=int,
        default=10,
        help="How many examples to print per category (default 10).",
    )
    args = ap.parse_args()

    cfg = load_config()
    gamma = GammaClient(cfg.gamma_api_base)

    print(f"GET {cfg.gamma_api_base}/markets ...")
    markets = gamma.fetch_active_markets(cfg.gamma_page_limit)
    outcomes = list(gamma.iter_outcomes(markets))
    print(
        f"Gamma returned: markets={len(markets)}, "
        f"priced_outcomes={len(outcomes)}"
    )

    counts: collections.Counter[str] = collections.Counter()
    city_hits = []
    weather_hits = []
    parse_misses = []
    parse_ok = []

    for o in outcomes:
        counts["total"] += 1
        q = o.get("question") or ""
        if detect_city(q):
            counts["city_match"] += 1
            city_hits.append(o)
            if looks_like_weather_question(q):
                counts["weather_match"] += 1
                weather_hits.append(o)

    for o in weather_hits:
        wm = parse_outcome(o)
        if wm is not None:
            counts["parsed_ok"] += 1
            parse_ok.append(wm)
        else:
            counts["weather_but_unparsed"] += 1
            reasons = []
            if not detect_city(o["question"]):
                reasons.append("no_city")
            if extract_target_date(o["question"]) is None:
                reasons.append("no_date_in_question")
            if (
                extract_bracket(o["outcome_label"]) is None
                and extract_bracket(o["question"]) is None
            ):
                reasons.append("no_bracket")
            parse_misses.append({
                "question": o["question"],
                "outcome_label": o["outcome_label"],
                "end_date": o.get("end_date"),
                "token_id": o.get("token_id"),
                "reasons": reasons,
            })

    print("\n=== Stage counts ===")
    for k in ("total", "city_match", "weather_match", "parsed_ok", "weather_but_unparsed"):
        print(f"  {k:<24} {counts[k]}")

    print("\n=== Parsed OK (first {}) ===".format(args.samples))
    for wm in parse_ok[: args.samples]:
        print(
            f"  {wm.city} {wm.target_date} {wm.bracket.describe():<14} "
            f"label={wm.outcome_label!r}"
        )

    print("\n=== City+weather but unparsed (first {}) ===".format(args.samples))
    for m in parse_misses[: args.samples]:
        print(f"  reasons={m['reasons']}")
        print(f"  Q: {m['question'][:140]!r}")
        print(f"     label={m['outcome_label']!r}  end_date={m['end_date']}")

    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(
                {
                    "counts": dict(counts),
                    "parse_misses": parse_misses,
                    "parsed_ok": [
                        {
                            "city": wm.city,
                            "target_date": wm.target_date.isoformat(),
                            "bracket": wm.bracket.describe(),
                            "label": wm.outcome_label,
                            "question": wm.question,
                            "token_id": wm.token_id,
                        }
                        for wm in parse_ok
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"\nFull diagnostic written to {args.json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
