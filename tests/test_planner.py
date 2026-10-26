from heatplanner.limits import M_REST, admissible_metabolic_rate
from heatplanner.planner import Task, log_to_csv_text, plan_day, stoppage_log_rows

HOURS = range(6, 19)
COOL_MORNING = {h: (24.0 if h < 9 else 29.0 if h < 16 else 27.0) for h in HOURS}
HOT = {h: 31.5 for h in HOURS}


def test_never_exceeds_hourly_metabolic_budget():
    tasks = [Task("heavy", 230, 3), Task("medium", 190, 3), Task("light", 110, 2)]
    plan = plan_day(COOL_MORNING, tasks)
    cost = {t.name: t.intensity - M_REST for t in tasks}
    for h, hp in plan.hours.items():
        spent = sum(m * cost[n] for n, m in hp.minutes.items())
        budget = 60 * (admissible_metabolic_rate(hp.wbgt_eff) - M_REST)
        assert spent <= budget + 1e-6
        assert sum(hp.minutes.values()) + hp.rest_minutes == 60


def test_no_work_scheduled_when_too_hot():
    plan = plan_day(HOT, [Task("heavy", 230, 4)])
    assert plan.total_scheduled_minutes() == 0
    assert plan.unmet["heavy"] == 240
    assert all(hp.status == "STOP" for hp in plan.hours.values())


def test_heavy_work_goes_to_cooler_hours():
    plan = plan_day(COOL_MORNING, [Task("heavy", 230, 2)])
    morning = sum(plan.hours[h].minutes.get("heavy", 0) for h in (6, 7, 8))
    assert morning == 120  # all of it fits in the cool morning


def test_scheduled_never_exceeds_requested():
    plan = plan_day(COOL_MORNING, [Task("heavy", 230, 1)])
    assert plan.scheduled["heavy"] <= plan.requested["heavy"] == 60


def test_buffer_and_clothing_make_plan_more_conservative():
    base = plan_day(COOL_MORNING, [Task("heavy", 230, 8)])
    safer = plan_day(COOL_MORNING, [Task("heavy", 230, 8)], cav=1.0, buffer=1.0)
    assert safer.total_scheduled_minutes() <= base.total_scheduled_minutes()


def test_unacclimatized_workers_get_less_work():
    acc = plan_day(COOL_MORNING, [Task("heavy", 230, 8)], acclimatized=True)
    new = plan_day(COOL_MORNING, [Task("heavy", 230, 8)], acclimatized=False)
    assert new.total_scheduled_minutes() <= acc.total_scheduled_minutes()


def test_stoppage_log_has_one_row_per_hour_and_csv():
    plan = plan_day(COOL_MORNING, [Task("heavy", 230, 2)])
    rows = stoppage_log_rows(plan, "2025-04-20", "Test site", True, 0.0, 0.0)
    assert len(rows) == len(HOURS)
    assert {"wbgt_effective_c", "limit_applied", "status", "min_heavy"} <= set(rows[0])
    text = log_to_csv_text(rows)
    assert text.splitlines()[0].startswith("date,site,hour_start")
