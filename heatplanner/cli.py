"""Command-line interface.

    python -m heatplanner.cli plan      -> tomorrow's work-rest plan + messages + stoppage log
    python -m heatplanner.cli backtest  -> compare schedules against actual weather
    python -m heatplanner.cli fetch     -> download real weather data from Open-Meteo
"""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

from . import backtest as bt
from .data import (CHENNAI, complete_days, fetch_open_meteo, hourly_wbgt, read_weather_csv,
                   write_weather_csv)
from .limits import PRESETS
from .messages import hour_allowances, merge_blocks, render_message
from .planner import Task, log_to_csv_text, plan_day, stoppage_log_rows

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_FORECAST = ROOT / "data" / "sample_forecast_SYNTHETIC.csv"
SAMPLE_ARCHIVE = ROOT / "data" / "sample_archive_SYNTHETIC.csv"


def cmd_plan(a):
    if a.live:
        weather = fetch_open_meteo("live", lat=a.lat, lon=a.lon)
        print("Using LIVE Open-Meteo forecast.")
    else:
        path = a.weather or SAMPLE_FORECAST
        weather = read_weather_csv(path)
        print(f"Using weather file: {path}")
    days = complete_days(hourly_wbgt(weather, a.lat, a.lon))
    if not days:
        raise SystemExit("No complete days found in the weather data.")
    if a.date:
        date = dt.date.fromisoformat(a.date)
        if date not in days:
            raise SystemExit(f"Date {date} not available. Choose one of: {', '.join(str(d) for d in sorted(days))}")
    else:
        date = sorted(days)[0] if not a.live else sorted(days)[min(1, len(days) - 1)]
    wb = days[date]
    acc = not a.unacclimatized
    tasks = [Task("heavy", PRESETS["heavy"], a.heavy_hours), Task("medium", PRESETS["medium"], a.medium_hours),
             Task("light", PRESETS["light"], a.light_hours)]
    plan = plan_day(wb, tasks, acc, a.cav, a.buffer)

    print(f"\nDate: {date} | Site: {a.site} | acclimatized: {acc} | clothing adj: {a.cav} C | buffer: {a.buffer} C\n")
    print(f"{'hour':<7}{'WBGT':>6}{'eff':>6}  {'status':<8}" + "".join(f"{t.name:>8}" for t in tasks) + f"{'rest':>6}")
    for h, hp in plan.hours.items():
        print(f"{h:02d}:00  {hp.wbgt:>6.1f}{hp.wbgt_eff:>6.1f}  {hp.status:<8}"
              + "".join(f"{hp.minutes.get(t.name, 0):>8}" for t in tasks) + f"{hp.rest_minutes:>6}")
    print("\nScheduled vs requested minutes:")
    for t in tasks:
        print(f"  {t.name:<7}{plan.scheduled[t.name]:>4} / {plan.requested[t.name]:<4} (unmet {plan.unmet[t.name]})")

    blocks = merge_blocks(hour_allowances(wb, acc, a.cav, a.buffer))
    for lang in (["en", "ta"] if a.lang == "both" else [a.lang]):
        print(f"\n--- Message ({lang}) ---")
        print(render_message(a.site, str(date), blocks, lang))

    out = Path(a.log)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(log_to_csv_text(stoppage_log_rows(plan, str(date), a.site, acc, a.cav, a.buffer)),
                   encoding="utf-8")
    print(f"\nStoppage log written to {out}")


def cmd_backtest(a):
    fc_path = a.forecast or SAMPLE_FORECAST
    ob_path = a.archive or SAMPLE_ARCHIVE
    print(f"Forecast file: {fc_path}\nArchive file : {ob_path}")
    if "SYNTHETIC" in str(fc_path).upper() or "SYNTHETIC" in str(ob_path).upper():
        print("\n*** WARNING: SYNTHETIC DATA. These numbers only test the code. They are NOT findings. ***\n")
    m = a.m_work if a.m_work else PRESETS["heavy"]
    results, meta = bt.run_from_files(fc_path, ob_path, m_work=m, hours_needed=a.hours, q=a.quantile,
                                      acclimatized=not a.unacclimatized, cav=a.cav)
    print(meta["note"])
    print(f"Calibrated buffer (q={meta['quantile']}): {meta['buffer_c']:.2f} C\n")
    print(bt.results_table(results))
    csv_path, png_path = bt.save_outputs(results, meta, a.out, a.label)
    print(f"\nSaved: {csv_path}\nSaved: {png_path}")


def cmd_fetch(a):
    Path(a.out).mkdir(parents=True, exist_ok=True)
    tag = f"{a.start}_{a.end}"
    for kind, name in (("forecast_history", "forecast"), ("archive", "archive")):
        print(f"Downloading {kind} ...")
        try:
            weather = fetch_open_meteo(kind, a.start, a.end, a.lat, a.lon)
        except Exception as e:  # network, DNS, rate limit, API change
            raise SystemExit(f"Download failed for '{kind}': {e}\nCheck your internet connection and the dates, "
                             "then try again (or try a shorter date range).")
        path = Path(a.out) / f"chennai_{name}_{tag}.csv"
        write_weather_csv(path, weather)
        print(f"  saved {len(weather)} hourly rows -> {path}")
    print("\nNow run:  python -m heatplanner.cli backtest --forecast data/chennai_forecast_"
          f"{tag}.csv --archive data/chennai_archive_{tag}.csv")


def main(argv=None):
    p = argparse.ArgumentParser(prog="heatplanner", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    pp = sub.add_parser("plan", help="make a plan for one day")
    pp.add_argument("--weather", help="forecast CSV (default: bundled synthetic sample)")
    pp.add_argument("--live", action="store_true", help="download the live forecast from Open-Meteo")
    pp.add_argument("--date", help="YYYY-MM-DD")
    pp.add_argument("--site", default="Demo site, Chennai")
    pp.add_argument("--heavy-hours", type=float, default=3.0)
    pp.add_argument("--medium-hours", type=float, default=3.0)
    pp.add_argument("--light-hours", type=float, default=2.0)
    pp.add_argument("--cav", type=float, default=0.0, help="clothing adjustment in C (0 cotton, +1 woven coverall)")
    pp.add_argument("--buffer", type=float, default=0.0, help="forecast safety buffer in C")
    pp.add_argument("--unacclimatized", action="store_true")
    pp.add_argument("--lang", choices=["en", "ta", "both"], default="both")
    pp.add_argument("--log", default="outputs/stoppage_log.csv")
    pp.add_argument("--lat", type=float, default=CHENNAI[0])
    pp.add_argument("--lon", type=float, default=CHENNAI[1])
    pp.set_defaults(func=cmd_plan)

    pb = sub.add_parser("backtest", help="compare schedules on past data")
    pb.add_argument("--forecast")
    pb.add_argument("--archive")
    pb.add_argument("--m-work", type=float, help="work intensity W/m2 (default heavy preset 230)")
    pb.add_argument("--hours", type=float, default=8.0)
    pb.add_argument("--quantile", type=float, default=0.9)
    pb.add_argument("--cav", type=float, default=0.0)
    pb.add_argument("--unacclimatized", action="store_true")
    pb.add_argument("--out", default="outputs")
    pb.add_argument("--label", default="backtest")
    pb.add_argument("--lat", type=float, default=CHENNAI[0])
    pb.add_argument("--lon", type=float, default=CHENNAI[1])
    pb.set_defaults(func=cmd_backtest)

    pf = sub.add_parser("fetch", help="download real weather data")
    pf.add_argument("--start", required=True, help="YYYY-MM-DD")
    pf.add_argument("--end", required=True, help="YYYY-MM-DD")
    pf.add_argument("--out", default="data")
    pf.add_argument("--lat", type=float, default=CHENNAI[0])
    pf.add_argument("--lon", type=float, default=CHENNAI[1])
    pf.set_defaults(func=cmd_fetch)

    a = p.parse_args(argv)
    a.func(a)


if __name__ == "__main__":
    main()
