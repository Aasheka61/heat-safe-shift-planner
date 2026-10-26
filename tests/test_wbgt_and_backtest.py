import datetime as dt
from pathlib import Path

from heatplanner import backtest as bt
from heatplanner.data import complete_days, hourly_wbgt, read_weather_csv
from heatplanner.wbgt import cos_zenith, wbgt_liljegren

DATA = Path(__file__).resolve().parent.parent / "data"


def test_noon_sun_is_overhead_in_chennai_in_april():
    noon_local = dt.datetime(2025, 4, 15, 12, 0)
    cz = cos_zenith(13.08, 80.27, noon_local - dt.timedelta(hours=5.5))
    assert cz > 0.95


def test_night_has_sun_below_horizon():
    cz = cos_zenith(13.08, 80.27, dt.datetime(2025, 4, 15, 23, 0) - dt.timedelta(hours=5.5))
    assert cz < 0


def test_wbgt_is_plausible_and_sun_raises_it():
    sun = wbgt_liljegren(35, 60, 1008, 3, 900, 630, 0.95)
    shade = wbgt_liljegren(35, 60, 1008, 3, 0, 0, -0.2)
    assert 30 < sun < 38
    assert sun > shade + 1.0


def test_wbgt_rises_with_humidity():
    dry = wbgt_liljegren(34, 40, 1008, 2, 800, 500, 0.9)
    humid = wbgt_liljegren(34, 85, 1008, 2, 800, 500, 0.9)
    assert humid > dry


def test_sample_files_load_and_have_full_days():
    fc = complete_days(hourly_wbgt(read_weather_csv(DATA / "sample_forecast_SYNTHETIC.csv")))
    ob = complete_days(hourly_wbgt(read_weather_csv(DATA / "sample_archive_SYNTHETIC.csv")))
    assert len(fc) == len(ob) == 30
    assert all(len(v) == 13 for v in fc.values())


def test_backtest_properties_on_synthetic_sample():
    results, meta = bt.run_from_files(DATA / "sample_forecast_SYNTHETIC.csv",
                                      DATA / "sample_archive_SYNTHETIC.csv")
    r = {x.name: x for x in results}
    assert meta["eval_days"] == 15 and meta["calibration_days"] == 15
    for x in results:
        assert x.safe + x.overload == x.scheduled
    assert r["planner_oracle"].overload == 0          # perfect forecast -> never over the limit
    assert r["planner_buffered"].overload <= r["planner_no_buffer"].overload
    assert r["status_quo_9_to_6"].scheduled == r["blanket_12_to_3"].scheduled == 8 * 60 * meta["eval_days"]


def test_buffer_is_never_negative():
    fc = {dt.date(2025, 1, d): {h: 30.0 for h in range(6, 19)} for d in range(1, 5)}
    ob = {dt.date(2025, 1, d): {h: 28.0 for h in range(6, 19)} for d in range(1, 5)}
    assert bt.calibrate_buffer(fc, ob, sorted(fc)) == 0.0
