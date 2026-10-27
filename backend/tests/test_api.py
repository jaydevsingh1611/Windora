"""API tests against the bundled January 2026 snapshot."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_default_analysis_covers_whole_pilot():
    body = client.get("/api/analysis").json()
    assert body["summary"]["count"] == 31 * 24  # 31 delivery days x 24 hourly targets
    assert body["runsUsed"] == 31  # one forecast run per delivery day under a gate
    lo, hi = body["horizonRange"]
    assert 0 < lo < hi <= 48


def test_series_has_half_hourly_actuals_and_hourly_forecasts():
    pts = client.get("/api/series", params={"start": "2026-01-15", "end": "2026-01-15"}).json()["points"]
    assert len(pts) == 48
    assert sum(p["forecast"] is not None for p in pts) == 24


def test_horizon_mode():
    body = client.get("/api/analysis", params={"mode": "horizon", "horizon": 4}).json()
    assert body["horizonRange"][0] >= 4


def test_rejects_out_of_scope_dates():
    assert client.get("/api/analysis", params={"start": "2026-03-01", "end": "2026-03-02"}).status_code == 422
    assert client.get("/api/analysis", params={"start": "2026-01-20", "end": "2026-01-10"}).status_code == 422
    assert client.get("/api/analysis", params={"horizon": 99}).status_code == 422
