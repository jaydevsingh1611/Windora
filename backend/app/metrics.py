"""Forecast error statistics. Pure functions, no I/O.

Sign convention: error = forecast - actual (MW).
  error > 0  -> wind under-delivered vs forecast -> the team was short and must buy more.
  error < 0  -> wind over-delivered -> the team bought too much.
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from .config import LONDON


@dataclass(frozen=True)
class Pair:
    target_time: datetime
    actual: float
    forecast: float
    horizon_h: float

    @property
    def error(self) -> float:
        return self.forecast - self.actual


def percentile(values: list[float], q: float) -> float:
    """Linear-interpolated percentile (same as numpy's default), q in [0, 100]."""
    if not values:
        return math.nan
    s = sorted(values)
    pos = (len(s) - 1) * q / 100
    lo, hi = math.floor(pos), math.ceil(pos)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def summarize(pairs: list[Pair]) -> dict:
    if not pairs:
        return {"count": 0}
    errors = [p.error for p in pairs]
    abs_errors = [abs(e) for e in errors]
    n = len(errors)
    mean_actual = sum(p.actual for p in pairs) / n
    mae = sum(abs_errors) / n
    return {
        "count": n,
        "mae": mae,
        "rmse": math.sqrt(sum(e * e for e in errors) / n),
        "bias": sum(errors) / n,
        "maePctOfMeanActual": 100 * mae / mean_actual if mean_actual else None,
        "meanActual": mean_actual,
        "p10": percentile(errors, 10),
        "p50": percentile(errors, 50),
        "p90": percentile(errors, 90),
        "p95AbsError": percentile(abs_errors, 95),
        "maxAbsError": max(abs_errors),
        # MW of extra cover that would have covered the wind shortfall in 90% of hours
        "shortfallCoverP90": max(0.0, percentile(errors, 90)),
        "shareOverForecast": sum(e > 0 for e in errors) / n,
    }


def _group_mae(pairs: list[Pair], key) -> list[dict]:
    groups: dict = defaultdict(list)
    for p in pairs:
        groups[key(p)].append(p.error)
    out = []
    for k in sorted(groups):
        errs = groups[k]
        out.append(
            {
                "key": k,
                "count": len(errs),
                "mae": sum(abs(e) for e in errs) / len(errs),
                "bias": sum(errs) / len(errs),
                "p10": percentile(errs, 10),
                "p90": percentile(errs, 90),
            }
        )
    return out


def by_hour_of_day(pairs: list[Pair]) -> list[dict]:
    return _group_mae(pairs, lambda p: p.target_time.astimezone(LONDON).hour)


def by_horizon_bucket(pairs: list[Pair], bucket_h: int = 4) -> list[dict]:
    rows = _group_mae(pairs, lambda p: int(p.horizon_h // bucket_h) * bucket_h)
    for r in rows:
        r["label"] = f"{r['key']}-{r['key'] + bucket_h}h"
    return rows


def by_delivery_day(pairs: list[Pair]) -> list[dict]:
    groups: dict = defaultdict(list)
    for p in pairs:
        groups[p.target_time.astimezone(LONDON).date().isoformat()].append(p)
    out = []
    for day in sorted(groups):
        ps = groups[day]
        worst = max(ps, key=lambda p: abs(p.error))
        out.append(
            {
                "day": day,
                "count": len(ps),
                "meanForecast": sum(p.forecast for p in ps) / len(ps),
                "meanActual": sum(p.actual for p in ps) / len(ps),
                "mae": sum(abs(p.error) for p in ps) / len(ps),
                "bias": sum(p.error for p in ps) / len(ps),
                "worstHour": worst.target_time.isoformat(),
                "worstError": worst.error,
            }
        )
    return out


def histogram(pairs: list[Pair], bin_mw: int = 500) -> list[dict]:
    counts: dict[int, int] = defaultdict(int)
    for p in pairs:
        counts[int(math.floor(p.error / bin_mw)) * bin_mw] += 1
    if not counts:
        return []
    lo, hi = min(counts), max(counts)
    return [{"binStart": b, "binEnd": b + bin_mw, "count": counts.get(b, 0)} for b in range(lo, hi + bin_mw, bin_mw)]
