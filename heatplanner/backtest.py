"""Backtest: compare work schedules against what the weather actually did.

Policies compared (all schedule 8 work-hours of the same task):
  status_quo_9_to_6   9:00-18:00 with a 13:00-14:00 lunch (no heat rule)
  blanket_12_to_3     work 7-12 and 15-18 (a fixed 12-3 pm break, Kerala-style)
  planner_no_buffer   our planner using the FORECAST only
  planner_buffered    our planner using the forecast + a safety buffer
  planner_oracle      our planner using the ACTUAL weather (upper bound, not achievable)

Metrics (minutes, summed over evaluation days):
  scheduled  minutes of work in the schedule
  safe       minutes within the allowed work-minutes for the ACTUAL conditions
  overload   scheduled - safe  (work done above the allowed fraction)

The buffer is calibrated on the first half of the days and everything is evaluated on the
second half, so the result is not tuned on the days it is judged on.
"""
from __future__ import annotations

from dataclasses import dataclass

from .data import WORK_HOURS, complete_days, hourly_wbgt, read_weather_csv
from .limits import allowed_minutes
from .planner import Task, plan_day

STATUS_QUO_HOURS = (9, 10, 11, 12, 14, 15, 16, 17)
BLANKET_HOURS = (7, 8, 9, 10, 11, 15, 16, 17)


@dataclass
class PolicyResult:
    name: str
    scheduled: int
    safe: int
    overload: int
    days: int
    days_with_overload: int
    worst_day_overload: int

    @property
    def safe_pct(self) -> float:
        return 100.0 * self.safe / self.scheduled if self.scheduled else 0.0


def evaluate_schedule(schedule: dict, observed: dict, m_work: float, acclimatized=True, cav=0.0):
    """schedule {hour: minutes}; observed {hour: WBGT}. Returns (scheduled, safe, overload)."""
    scheduled = safe = 0
    for h, mins in schedule.items():
        cap = allowed_minutes(m_work, observed[h] + cav, acclimatized)
        scheduled += mins
        safe += min(mins, cap)
    return scheduled, safe, scheduled - safe


def planner_schedule(wbgt_by_hour: dict, m_work: float, hours_needed: float = 8.0,
                     acclimatized=True, cav=0.0, buffer=0.0) -> dict:
    plan = plan_day(wbgt_by_hour, [Task("work", m_work, hours_needed)], acclimatized, cav, buffer)
    return {h: hp.minutes.get("work", 0) for h, hp in plan.hours.items()}


def calibrate_buffer(forecast_days: dict, observed_days: dict, dates: list, q: float = 0.9) -> float:
    """q-quantile of (observed - forecast) WBGT errors, never below 0."""
    errs = sorted(observed_days[d][h] - forecast_days[d][h] for d in dates for h in WORK_HOURS)
    if not errs:
        return 0.0
    return max(0.0, errs[int(round(q * (len(errs) - 1)))])


def run_backtest(forecast_days: dict, observed_days: dict, m_work: float = 230.0,
                 hours_needed: float = 8.0, q: float = 0.9, acclimatized=True, cav=0.0):
    dates = sorted(set(forecast_days) & set(observed_days))
    if len(dates) < 4:
        calib, evald = dates, dates
        split_note = "Fewer than 4 common days: buffer calibrated and evaluated on the same days."
    else:
        half = len(dates) // 2
        calib, evald = dates[:half], dates[half:]
        split_note = f"Buffer calibrated on {len(calib)} days, evaluated on {len(evald)} other days."
    buffer = calibrate_buffer(forecast_days, observed_days, calib, q)

    fixed = {"status_quo_9_to_6": {h: 60 for h in STATUS_QUO_HOURS},
             "blanket_12_to_3": {h: 60 for h in BLANKET_HOURS}}
    names = ["status_quo_9_to_6", "blanket_12_to_3", "planner_no_buffer", "planner_buffered", "planner_oracle"]
    acc = {n: [0, 0, 0, 0, 0] for n in names}  # scheduled, safe, overload, days_over, worst

    for d in evald:
        fc, ob = forecast_days[d], observed_days[d]
        scheds = dict(fixed)
        scheds["planner_no_buffer"] = planner_schedule(fc, m_work, hours_needed, acclimatized, cav, 0.0)
        scheds["planner_buffered"] = planner_schedule(fc, m_work, hours_needed, acclimatized, cav, buffer)
        scheds["planner_oracle"] = planner_schedule(ob, m_work, hours_needed, acclimatized, cav, 0.0)
        for n in names:
            s, safe, over = evaluate_schedule(scheds[n], ob, m_work, acclimatized, cav)
            a = acc[n]
            a[0] += s; a[1] += safe; a[2] += over
            a[3] += 1 if over > 0 else 0
            a[4] = max(a[4], over)
    results = [PolicyResult(n, *acc[n][:3], len(evald), acc[n][3], acc[n][4]) for n in names]
    meta = {"buffer_c": buffer, "eval_days": len(evald), "calibration_days": len(calib),
            "note": split_note, "m_work": m_work, "quantile": q}
    return results, meta


def run_from_files(forecast_csv, archive_csv, **kw):
    fc = complete_days(hourly_wbgt(read_weather_csv(forecast_csv)))
    ob = complete_days(hourly_wbgt(read_weather_csv(archive_csv)))
    return run_backtest(fc, ob, **kw)


def results_table(results: list) -> str:
    head = f"{'policy':<20}{'scheduled':>10}{'safe':>8}{'overload':>10}{'safe %':>8}{'days over':>10}{'worst day':>10}"
    lines = [head, "-" * len(head)]
    for r in results:
        lines.append(f"{r.name:<20}{r.scheduled:>10}{r.safe:>8}{r.overload:>10}{r.safe_pct:>8.1f}"
                     f"{r.days_with_overload:>7}/{r.days:<3}{r.worst_day_overload:>10}")
    return "\n".join(lines)


def save_outputs(results: list, meta: dict, out_dir="outputs", label="backtest"):
    import csv
    from pathlib import Path
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / f"{label}_summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["policy", "scheduled_min", "safe_min", "overload_min", "safe_pct",
                    "days_with_overload", "eval_days", "worst_day_overload_min"])
        for r in results:
            w.writerow([r.name, r.scheduled, r.safe, r.overload, round(r.safe_pct, 1),
                        r.days_with_overload, r.days, r.worst_day_overload])
    names = [r.name.replace("_", "\n") for r in results]
    days = max(1, results[0].days)
    fig, ax = plt.subplots(figsize=(10, 4.5))
    xs = range(len(results))
    ax.bar([x - 0.2 for x in xs], [r.safe / days for r in results], 0.4, label="safe minutes/day", color="#2e7d32")
    ax.bar([x + 0.2 for x in xs], [r.overload / days for r in results], 0.4, label="overload minutes/day", color="#c62828")
    ax.set_xticks(list(xs))
    ax.set_xticklabels(names, fontsize=8)
    ax.set_ylabel("minutes per day")
    ax.set_title(f"Heavy work ({meta['m_work']:.0f} W/m2): safe vs overload minutes, "
                 f"{meta['eval_days']} evaluation days")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / f"{label}_chart.png", dpi=150)
    plt.close(fig)
    return out / f"{label}_summary.csv", out / f"{label}_chart.png"
