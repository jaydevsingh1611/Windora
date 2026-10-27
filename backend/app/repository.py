"""Data access: bundled snapshot first, live Elexon as fallback. Loaded once per process."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache

from . import config
from .elexon import fetch_wind_actuals, fetch_wind_forecasts
from .forecast import ForecastIndex

log = logging.getLogger(__name__)


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(config.UTC)


@dataclass
class Dataset:
    actuals: dict[datetime, float]  # half-hourly, keyed by startTime (UTC)
    forecasts: ForecastIndex
    run_times: list[datetime]  # distinct forecast publish times
    source: str
    fetched_at: str


def _from_rows(actual_rows, forecast_rows, source: str, fetched_at: str) -> Dataset:
    actuals = {parse_ts(t): float(g) for t, g in actual_rows}
    parsed = [(parse_ts(p), parse_ts(t), float(g)) for p, t, g in forecast_rows]
    return Dataset(
        actuals=actuals,
        forecasts=ForecastIndex(parsed),
        run_times=sorted({p for p, _, _ in parsed}),
        source=source,
        fetched_at=fetched_at,
    )


def _load_live() -> Dataset:
    actuals = fetch_wind_actuals(config.ACTUALS_SETTLEMENT_FROM, config.ACTUALS_SETTLEMENT_TO)
    forecasts = fetch_wind_forecasts(config.FORECAST_PUBLISH_FROM, config.FORECAST_PUBLISH_TO)
    return _from_rows(
        [(r["startTime"], r["generation"]) for r in actuals],
        [(r["publishTime"], r["startTime"], r["generation"]) for r in forecasts],
        source="live",
        fetched_at=datetime.now(config.UTC).isoformat(timespec="seconds"),
    )


@lru_cache(maxsize=1)
def get_dataset() -> Dataset:
    if config.SNAPSHOT_PATH.exists():
        raw = json.loads(config.SNAPSHOT_PATH.read_text())
        return _from_rows(raw["actuals"], raw["forecasts"], "snapshot", raw.get("fetchedAt", ""))
    log.warning("Snapshot %s missing; fetching live from Elexon", config.SNAPSHOT_PATH)
    return _load_live()
