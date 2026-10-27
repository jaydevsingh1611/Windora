"""Scope of the pilot: day-ahead purchase decisions made during January 2026.

A decision made on day D-1 buys power for delivery day D, so decisions taken
1-31 Jan 2026 cover delivery days 2 Jan - 1 Feb 2026 (UK local days).
"""
from __future__ import annotations

from datetime import date, datetime, time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

LONDON = ZoneInfo("Europe/London")
UTC = timezone.utc

DELIVERY_START = date(2026, 1, 2)
DELIVERY_END = date(2026, 2, 1)  # inclusive

# GB day-ahead auction gate closure (EPEX/Nord Pool hourly auctions close ~09:20-09:50 UK time)
DEFAULT_GATE = time(9, 20)
DEFAULT_HORIZON_H = 24.0
MAX_HORIZON_H = 48.0

# Forecast runs we need: anything that could be "latest" for the first delivery
# day under a 48h horizon, through to the end of the last delivery day.
FORECAST_PUBLISH_FROM = datetime(2025, 12, 29, 0, 0, tzinfo=UTC)
FORECAST_PUBLISH_TO = datetime(2026, 2, 2, 0, 0, tzinfo=UTC)
ACTUALS_SETTLEMENT_FROM = date(2026, 1, 1)
ACTUALS_SETTLEMENT_TO = date(2026, 2, 2)

SNAPSHOT_PATH = Path(__file__).resolve().parent.parent / "data" / "snapshot_jan2026.json"
