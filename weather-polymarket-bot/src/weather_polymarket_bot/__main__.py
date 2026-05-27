"""CLI entry point.

    python -m weather_polymarket_bot           # single scan
    python -m weather_polymarket_bot --loop    # rescan every POLL_INTERVAL_SEC

There is no `--live` flag. Live trading is intentionally not wired up in
v1; see the TODO section of README.md.
"""

from __future__ import annotations

import argparse
import logging
import sys

from .config import load_config
from .scanner import Scanner


def _configure_logging(level_name: str) -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="weather-polymarket-bot",
        description="Paper-trading scanner for Polymarket weather markets.",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Re-scan every POLL_INTERVAL_SEC seconds (default: single pass).",
    )
    args = parser.parse_args(argv)

    cfg = load_config()
    _configure_logging(cfg.log_level)

    print(
        "weather-polymarket-bot starting | paper-trading mode "
        "(no real funds will be moved)",
        flush=True,
    )

    scanner = Scanner(cfg)
    if args.loop:
        scanner.run_forever()
    else:
        scanner.run_once()
    return 0


if __name__ == "__main__":
    sys.exit(main())
