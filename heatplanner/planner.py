"""Shift planner: turns hourly WBGT into a work-rest schedule per task.

For each hour the ISO limit gives a *metabolic budget*:   60 * (M_admissible - 65)
Every minute of work at intensity M costs (M - 65) of that budget. Tasks are placed heaviest
first into the coolest hours, then lighter tasks fill what is left. Minutes are rounded down
to multiples of `step` (default 5), so the schedule never exceeds the limit.
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass

from .limits import M_REST, admissible_metabolic_rate, limit_description, status


@dataclass(frozen=True)
class Task:
    name: str
    intensity: float  # W/m2
    hours: float      # required work-hours for the day


@dataclass
class HourPlan:
    hour: int
    wbgt: float
    wbgt_eff: float
    m_adm: float
    minutes: dict
    rest_minutes: int
    status: str
    limit: str


@dataclass
class PlanResult:
    hours: dict          # {hour: HourPlan}
    requested: dict      # {task name: minutes requested}
    unmet: dict          # {task name: minutes that could not be scheduled safely}

    @property
    def scheduled(self) -> dict:
        return {k: self.requested[k] - self.unmet[k] for k in self.requested}

    def total_scheduled_minutes(self) -> int:
        return sum(self.scheduled.values())


def plan_day(wbgt_by_hour: dict, tasks: list, acclimatized: bool = True,
             cav: float = 0.0, buffer: float = 0.0, step: int = 5) -> PlanResult:
    """wbgt_by_hour {hour: WBGT C}; cav = clothing adjustment (C); buffer = forecast safety margin (C)."""
    eff = {h: w + cav + buffer for h, w in wbgt_by_hour.items()}
    m_adm = {h: admissible_metabolic_rate(e, acclimatized) for h, e in eff.items()}
    budget = {h: 60.0 * (m_adm[h] - M_REST) for h in eff}
    used = {h: 0 for h in eff}
    minutes = {h: {} for h in eff}
    requested, unmet = {}, {}

    for task in sorted(tasks, key=lambda t: -t.intensity):
        need = int(round(task.hours * 60))
        requested[task.name] = need
        cost = max(0.0, task.intensity - M_REST)
        for h in sorted(eff, key=lambda x: (-budget[x], x)):  # coolest hours first
            if need <= 0:
                break
            room = 60 - used[h]
            by_budget = room if cost == 0 else int(budget[h] // cost)
            take = (min(need, room, by_budget) // step) * step
            if take > 0:
                minutes[h][task.name] = minutes[h].get(task.name, 0) + take
                used[h] += take
                budget[h] -= take * cost
                need -= take
        unmet[task.name] = need

    hours = {h: HourPlan(h, wbgt_by_hour[h], eff[h], m_adm[h], minutes[h], 60 - used[h],
                         status(eff[h], acclimatized), limit_description(eff[h], acclimatized))
             for h in sorted(eff)}
    return PlanResult(hours, requested, unmet)


def stoppage_log_rows(plan: PlanResult, date: str, site: str, acclimatized: bool,
                      cav: float, buffer: float) -> list:
    """One row per hour: inputs, limit applied, decision. Intended as an auditable record."""
    names = list(plan.requested)
    rows = []
    for h, hp in plan.hours.items():
        row = {"date": date, "site": site, "hour_start": f"{h:02d}:00",
               "wbgt_model_c": round(hp.wbgt, 2), "clothing_adj_c": cav, "forecast_buffer_c": buffer,
               "wbgt_effective_c": round(hp.wbgt_eff, 2), "acclimatized": acclimatized,
               "max_avg_metabolic_rate_w_m2": hp.m_adm, "status": hp.status, "limit_applied": hp.limit}
        for n in names:
            row[f"min_{n}"] = hp.minutes.get(n, 0)
        row["rest_minutes"] = hp.rest_minutes
        rows.append(row)
    return rows


def log_to_csv_text(rows: list) -> str:
    if not rows:
        return ""
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()
