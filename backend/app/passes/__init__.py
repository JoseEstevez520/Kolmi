"""The AI passes.

`run_daily_pass` is loaded lazily so that `python -m app.passes.daily` does not
import the module twice (once through the package, once as `__main__`).
"""

from __future__ import annotations

from typing import Any

__all__ = ["run_daily_pass"]


def __getattr__(name: str) -> Any:
    if name == "run_daily_pass":
        from .daily import run_daily_pass

        return run_daily_pass
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
