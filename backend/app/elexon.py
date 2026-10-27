"""Thin client for the Elexon BMRS Insights API (public, no API key).

Only two datasets are used:
  * FUELHH  - half-hourly outturn generation by fuel type (we keep fuelType=WIND)
  * WINDFOR - national wind generation forecasts (hourly targets, ~8 runs per day)
"""
from __future__ import annotations

import time
from datetime import date, datetime

import httpx

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
TIMEOUT = httpx.Timeout(30.0)


def _get(path: str, params: dict, retries: int = 3) -> list[dict]:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            resp = httpx.get(f"{BASE_URL}/{path}", params=params, timeout=TIMEOUT)
            resp.raise_for_status()
            body = resp.json()
            # /stream endpoints return a bare list; non-stream ones wrap in {"data": [...]}
            return body["data"] if isinstance(body, dict) else body
        except (httpx.HTTPError, ValueError) as exc:
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Elexon request failed for {path}: {last_error}")


def fetch_wind_actuals(settlement_from: date, settlement_to: date) -> list[dict]:
    """Half-hourly wind outturn. Returns [{"startTime": iso, "generation": MW}]."""
    rows = _get(
        "FUELHH/stream",
        {
            "settlementDateFrom": settlement_from.isoformat(),
            "settlementDateTo": settlement_to.isoformat(),
            "fuelType": "WIND",
        },
    )
    return [
        {"startTime": r["startTime"], "generation": r["generation"]}
        for r in rows
        if r.get("fuelType") == "WIND"
    ]


def fetch_wind_forecasts(publish_from: datetime, publish_to: datetime) -> list[dict]:
    """All forecast runs published in the window.

    Returns [{"publishTime": iso, "startTime": iso, "generation": MW}].
    """
    rows = _get(
        "WINDFOR/stream",
        {
            "publishDateTimeFrom": publish_from.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "publishDateTimeTo": publish_to.strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    )
    return [
        {"publishTime": r["publishTime"], "startTime": r["startTime"], "generation": r["generation"]}
        for r in rows
    ]
