import math
from datetime import datetime, timezone

import pytest

from app.metrics import Pair, by_horizon_bucket, histogram, percentile, summarize

T = datetime(2026, 1, 10, 12, tzinfo=timezone.utc)


def pairs(*fa: tuple[float, float], horizon: float = 20.0) -> list[Pair]:
    return [Pair(T, actual=a, forecast=f, horizon_h=horizon) for f, a in fa]


def test_percentile_matches_linear_interpolation():
    assert percentile([1, 2, 3, 4], 50) == 2.5
    assert percentile([10], 90) == 10
    assert math.isnan(percentile([], 50))


def test_summary_hand_computed():
    # errors (forecast - actual): +100, -100, +300
    s = summarize(pairs((1100, 1000), (900, 1000), (1300, 1000)))
    assert s["count"] == 3
    assert s["mae"] == pytest.approx(500 / 3)
    assert s["bias"] == pytest.approx(100)
    assert s["rmse"] == pytest.approx(math.sqrt((100**2 + 100**2 + 300**2) / 3))
    assert s["maePctOfMeanActual"] == pytest.approx(100 * (500 / 3) / 1000)
    assert s["maxAbsError"] == 300
    assert s["shareOverForecast"] == pytest.approx(2 / 3)


def test_shortfall_cover_is_never_negative():
    s = summarize(pairs((900, 1000), (800, 1000)))  # always under-forecast
    assert s["shortfallCoverP90"] == 0.0


def test_empty_summary():
    assert summarize([]) == {"count": 0}


def test_horizon_buckets():
    rows = by_horizon_bucket(pairs((1100, 1000), horizon=5.5) + pairs((1200, 1000), horizon=17.5))
    assert [(r["label"], r["mae"]) for r in rows] == [("4-8h", 100), ("16-20h", 200)]


def test_histogram_fills_empty_bins():
    h = histogram(pairs((1000, 0), (-1000, 0)), bin_mw=500)
    assert [b["binStart"] for b in h] == [-1000, -500, 0, 500, 1000]
    assert sum(b["count"] for b in h) == 2
