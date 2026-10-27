from datetime import datetime, time, timezone

from app.forecast import ForecastIndex, gate_cutoff, select_forecasts

UTC = timezone.utc


def ts(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=UTC)


TARGET = ts("2026-01-10T12:00")
INDEX = ForecastIndex(
    [
        (ts("2026-01-08T22:30"), TARGET, 100.0),
        (ts("2026-01-09T07:30"), TARGET, 200.0),
        (ts("2026-01-09T09:30"), TARGET, 300.0),  # after a 09:20 gate
        (ts("2026-01-10T13:30"), TARGET, 999.0),  # published after the target -> never usable
    ]
)


def test_gate_cutoff_winter_is_utc():
    assert gate_cutoff(TARGET, time(9, 20)) == ts("2026-01-09T09:20")


def test_gate_cutoff_uses_uk_local_day_in_summer():
    # 23:30 UTC on 30 Jun is 00:30 BST on 1 Jul -> delivery day 1 Jul, gate 30 Jun 09:20 BST = 08:20 UTC
    assert gate_cutoff(ts("2026-06-30T23:30"), time(9, 20)) == ts("2026-06-30T08:20")


def test_gate_mode_picks_latest_run_before_gate():
    hit = select_forecasts(INDEX, [TARGET], "gate", time(9, 20), 0)[TARGET]
    assert hit.generation == 200.0
    assert hit.horizon_h == 28.5


def test_later_gate_picks_later_run():
    hit = select_forecasts(INDEX, [TARGET], "gate", time(10, 0), 0)[TARGET]
    assert hit.generation == 300.0


def test_horizon_mode_respects_minimum_lead_time():
    assert select_forecasts(INDEX, [TARGET], "horizon", time(9, 20), 24)[TARGET].generation == 300.0
    assert select_forecasts(INDEX, [TARGET], "horizon", time(9, 20), 30)[TARGET].generation == 100.0


def test_horizon_zero_never_uses_forecast_published_after_target():
    assert select_forecasts(INDEX, [TARGET], "horizon", time(9, 20), 0)[TARGET].generation == 300.0


def test_no_forecast_available_is_skipped():
    assert select_forecasts(INDEX, [TARGET], "horizon", time(9, 20), 48) == {}
    assert select_forecasts(INDEX, [ts("2026-01-11T00:00")], "gate", time(9, 20), 0) == {}
