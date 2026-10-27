"""Pick the forecast a trader would actually have had when buying day-ahead.

Two selection rules:
  * gate    - latest run published at/before the auction gate on D-1 (UK local time).
              This mirrors the real decision: every hour of delivery day D uses the
              same forecast run, so horizons vary across the day (~16-40h at 09:20).
  * horizon - latest run published at least H hours before each target time.
              Useful for "how good is a 24h-ahead forecast?" style questions.

All functions are pure and operate on timezone-aware UTC datetimes.
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Literal

from .config import LONDON, UTC

Mode = Literal["gate", "horizon"]


@dataclass(frozen=True)
class SelectedForecast:
    target_time: datetime
    publish_time: datetime
    generation: float

    @property
    def horizon_h(self) -> float:
        return (self.target_time - self.publish_time).total_seconds() / 3600


class ForecastIndex:
    """Forecast runs indexed by target time, each list sorted by publish time."""

    def __init__(self, rows: list[tuple[datetime, datetime, float]]):
        by_target: dict[datetime, list[tuple[datetime, float]]] = {}
        for publish, target, gen in rows:
            by_target.setdefault(target, []).append((publish, gen))
        self._publish: dict[datetime, list[datetime]] = {}
        self._gen: dict[datetime, list[float]] = {}
        for target, runs in by_target.items():
            runs.sort()
            self._publish[target] = [p for p, _ in runs]
            self._gen[target] = [g for _, g in runs]

    def targets(self) -> list[datetime]:
        return sorted(self._publish)

    def runs_for(self, target: datetime) -> list[tuple[datetime, float]]:
        return list(zip(self._publish.get(target, []), self._gen.get(target, [])))

    def latest_before(self, target: datetime, cutoff: datetime) -> SelectedForecast | None:
        """Latest forecast for `target` with publish_time <= cutoff (and <= target)."""
        publishes = self._publish.get(target)
        if not publishes:
            return None
        i = bisect_right(publishes, min(cutoff, target)) - 1
        if i < 0:
            return None
        return SelectedForecast(target, publishes[i], self._gen[target][i])


def gate_cutoff(target: datetime, gate: time) -> datetime:
    """Gate closure (UTC) for the delivery day that `target` falls in (UK local day)."""
    delivery_day = target.astimezone(LONDON).date()
    decision_day = delivery_day - timedelta(days=1)
    return datetime.combine(decision_day, gate, tzinfo=LONDON).astimezone(UTC)


def select_forecasts(
    index: ForecastIndex,
    targets: list[datetime],
    mode: Mode,
    gate: time,
    horizon_h: float,
) -> dict[datetime, SelectedForecast]:
    selected: dict[datetime, SelectedForecast] = {}
    for target in targets:
        if mode == "gate":
            cutoff = gate_cutoff(target, gate)
        else:
            cutoff = target - timedelta(hours=horizon_h)
        hit = index.latest_before(target, cutoff)
        if hit is not None:
            selected[target] = hit
    return selected
