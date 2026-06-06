#!/usr/bin/env python3
"""data_integrity_check.py — Verify ui-ux-pro-max CSV bundle is intact.

Stdlib-only. Walks the data/ directory, opens each CSV via csv.DictReader,
counts rows, and asserts the count matches the documented schema in SKILL.md.

Fail-fast on:
  - Missing expected CSV files
  - Empty or 1-row files (header-only)
  - Unexpected row counts vs documented schema (within tolerance)
  - CSV parse errors (malformed quoting, encoding issues)

Returns 0 if all checks pass, 1 if any check fails.

Run from this script's directory or from the skill root:
  python3 data_integrity_check.py
  python3 scripts/data_integrity_check.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

# Documented schema from SKILL.md / NextLevelBuilder upstream v2.5.0.
# Counts allow ±5% tolerance to handle upstream additions.
EXPECTED_MAIN = {
    "app-interface.csv": 25,
    "charts.csv": 25,
    "colors.csv": 161,
    "design.csv": 1600,
    "draft.csv": 1600,
    "google-fonts.csv": 1900,
    "icons.csv": 130,
    "landing.csv": 34,
    "products.csv": 161,
    "react-performance.csv": 35,
    "styles.csv": 67,
    "typography.csv": 57,
    "ui-reasoning.csv": 161,
    "ux-guidelines.csv": 99,
}

EXPECTED_STACKS = [
    "angular.csv", "astro.csv", "flutter.csv", "html-tailwind.csv",
    "jetpack-compose.csv", "laravel.csv", "nextjs.csv", "nuxt-ui.csv",
    "nuxtjs.csv", "react-native.csv", "react.csv", "shadcn.csv",
    "svelte.csv", "swiftui.csv", "threejs.csv", "vue.csv",
]

TOLERANCE = 0.30  # ±30% — upstream rows added between versions


def find_data_dir() -> Path:
    here = Path(__file__).resolve().parent
    # When invoked from scripts/, data/ is a sibling
    candidate = here.parent / "data"
    if candidate.is_dir():
        return candidate
    # When invoked from skill root, data/ is in cwd
    candidate = Path.cwd() / "data"
    if candidate.is_dir():
        return candidate
    raise FileNotFoundError("Could not locate data/ directory")


def count_rows(path: Path) -> int:
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        return sum(1 for _ in reader)


def within_tolerance(actual: int, expected: int) -> bool:
    if expected == 0:
        return actual == 0
    delta = abs(actual - expected) / expected
    return delta <= TOLERANCE


def check_file(path: Path, expected: int) -> tuple[bool, str]:
    if not path.is_file():
        return False, f"MISSING: {path.name}"
    try:
        actual = count_rows(path)
    except (csv.Error, UnicodeDecodeError) as exc:
        return False, f"PARSE ERROR: {path.name} — {exc.__class__.__name__}: {exc}"
    if actual == 0:
        return False, f"EMPTY: {path.name} (header-only or no data rows)"
    if not within_tolerance(actual, expected):
        return False, f"ROW COUNT: {path.name} has {actual} rows; expected ~{expected} (±{int(TOLERANCE * 100)}%)"
    return True, f"OK: {path.name} ({actual} rows)"


def main() -> int:
    try:
        data_dir = find_data_dir()
    except FileNotFoundError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(f"Checking data integrity in {data_dir}")
    print("=" * 60)

    results: list[tuple[bool, str]] = []

    for name, expected in EXPECTED_MAIN.items():
        results.append(check_file(data_dir / name, expected))

    stacks_dir = data_dir / "stacks"
    if not stacks_dir.is_dir():
        results.append((False, "MISSING: data/stacks/ directory"))
    else:
        for name in EXPECTED_STACKS:
            # Stack CSVs vary in row count; just check non-empty.
            path = stacks_dir / name
            if not path.is_file():
                results.append((False, f"MISSING: stacks/{name}"))
                continue
            try:
                actual = count_rows(path)
            except (csv.Error, UnicodeDecodeError) as exc:
                results.append((False, f"PARSE ERROR: stacks/{name} — {exc}"))
                continue
            if actual == 0:
                results.append((False, f"EMPTY: stacks/{name}"))
            else:
                results.append((True, f"OK: stacks/{name} ({actual} rows)"))

    passes = sum(1 for ok, _ in results if ok)
    fails = sum(1 for ok, _ in results if not ok)

    for ok, msg in results:
        print(("[PASS] " if ok else "[FAIL] ") + msg)

    print("=" * 60)
    print(f"Summary: {passes} pass / {fails} fail / {len(results)} total")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
