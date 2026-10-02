from __future__ import annotations

import argparse
import json

from .daily import run_daily_pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Kolmi daily pass.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ask the gatekeeper what it would do and write nothing.",
    )
    args = parser.parse_args()

    summary = run_daily_pass(dry_run=args.dry_run)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
