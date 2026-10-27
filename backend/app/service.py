"""Glue between the data, forecast selection and metrics. Returns JSON-ready dicts."""
from __future__ import annotations

from datetime import date, datetime

from . import metrics
from .config import LONDON, MAX_HORIZON_H
from .forecast import select_forecasts
from .metrics import Pair
from .models import AnalysisParams
from .repository import Dataset


def _in_days(t: datetime, start: date, end: date) -> bool:
    return start <= t.astimezone(LONDON).date() <= end


def _iso(t: datetime) -> str:
    return t.isoformat().replace("+00:00", "Z")


def _selected_pairs(ds: Dataset, p: AnalysisParams):
    targets = [t for t in ds.forecasts.targets() if _in_days(t, p.start, p.end)]
    selected = select_forecasts(ds.forecasts, targets, p.mode, p.gate, p.horizon)
    pairs = [
        Pair(t, ds.actuals[t], s.generation, s.horizon_h)
        for t, s in sorted(selected.items())
        if t in ds.actuals
    ]
    return selected, pairs


def series(ds: Dataset, p: AnalysisParams) -> dict:
    selected, _ = _selected_pairs(ds, p)
    times = sorted({t for t in ds.actuals if _in_days(t, p.start, p.end)} | set(selected))
    points = []
    for t in times:
        s = selected.get(t)
        points.append(
            {
                "time": _iso(t),
                "actual": ds.actuals.get(t),
                "forecast": s.generation if s else None,
                "publishTime": _iso(s.publish_time) if s else None,
                "horizonH": round(s.horizon_h, 2) if s else None,
            }
        )
    return {"points": points}


def analysis(ds: Dataset, p: AnalysisParams) -> dict:
    selected, pairs = _selected_pairs(ds, p)
    runs = sorted({s.publish_time for s in selected.values()})
    horizons = [pr.horizon_h for pr in pairs]
    return {
        "summary": metrics.summarize(pairs),
        "horizonRange": [min(horizons), max(horizons)] if horizons else None,
        "runsUsed": len(runs),
        "byHour": metrics.by_hour_of_day(pairs),
        "byDay": metrics.by_delivery_day(pairs),
        "histogram": metrics.histogram(pairs),
    }


def horizon_accuracy(ds: Dataset, start: date, end: date, bucket_h: int = 4) -> dict:
    """Accuracy of *every* forecast run by lead time - shows how error grows with horizon."""
    pairs = []
    for t in ds.forecasts.targets():
        if t not in ds.actuals or not _in_days(t, start, end):
            continue
        for publish, gen in ds.forecasts.runs_for(t):
            h = (t - publish).total_seconds() / 3600
            if 0 <= h <= MAX_HORIZON_H:
                pairs.append(Pair(t, ds.actuals[t], gen, h))
    return {"buckets": metrics.by_horizon_bucket(pairs, bucket_h)}
