"""Pull the January 2026 window from Elexon and store it as a compact JSON snapshot.

Usage (from backend/):  python -m scripts.refresh_snapshot
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from app import config
from app.elexon import fetch_wind_actuals, fetch_wind_forecasts


def main() -> None:
    actuals = fetch_wind_actuals(config.ACTUALS_SETTLEMENT_FROM, config.ACTUALS_SETTLEMENT_TO)
    forecasts = fetch_wind_forecasts(config.FORECAST_PUBLISH_FROM, config.FORECAST_PUBLISH_TO)
    snapshot = {
        "source": "https://data.elexon.co.uk/bmrs/api/v1/datasets (FUELHH fuelType=WIND, WINDFOR)",
        "fetchedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        # compact row format keeps the file ~1 MB
        "actuals": sorted([r["startTime"], r["generation"]] for r in actuals),
        "forecasts": sorted([r["publishTime"], r["startTime"], r["generation"]] for r in forecasts),
    }
    config.SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    config.SNAPSHOT_PATH.write_text(json.dumps(snapshot, separators=(",", ":")))
    print(f"wrote {len(actuals)} actuals, {len(forecasts)} forecasts -> {config.SNAPSHOT_PATH}")


if __name__ == "__main__":
    main()
