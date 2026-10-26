"""Heat-Safe Shift Planner: Streamlit demo.   Run:  streamlit run app.py"""
import datetime as dt
from pathlib import Path

import pandas as pd
import streamlit as st

from heatplanner import backtest as bt
from heatplanner.data import CHENNAI, complete_days, fetch_open_meteo, hourly_wbgt, read_weather_csv
from heatplanner.limits import PRESETS, REF_ACCLIMATIZED, REF_UNACCLIMATIZED
from heatplanner.messages import hour_allowances, merge_blocks, render_message
from heatplanner.planner import Task, log_to_csv_text, plan_day, stoppage_log_rows

DATA = Path(__file__).parent / "data"
SAMPLE_FC = DATA / "sample_forecast_SYNTHETIC.csv"

st.set_page_config(page_title="Heat-Safe Shift Planner", layout="wide")
st.title("Heat-Safe Shift Planner")
st.caption("Hack for Social Cause | next-day work-rest schedules for construction sites in Tamil Nadu")
st.warning("Decision-support prototype. ISO limits were taken from secondary sources and the WBGT comes from "
           "a weather model, not a site sensor. Validate before real use and keep a safety officer in the loop.")


@st.cache_data(show_spinner=False)
def load_csv_days(path: str):
    return complete_days(hourly_wbgt(read_weather_csv(path)))


@st.cache_data(show_spinner=False, ttl=1800)
def load_live_days():
    return complete_days(hourly_wbgt(fetch_open_meteo("live", lat=CHENNAI[0], lon=CHENNAI[1])))


# ---------------- sidebar ----------------
st.sidebar.header("Inputs")
source = st.sidebar.radio("Weather source", ["Offline sample (SYNTHETIC)", "Live forecast (Open-Meteo, internet)",
                                              "Upload CSV"])
site = st.sidebar.text_input("Site name", "Demo site, Chennai")
acclimatized = st.sidebar.checkbox("Workers are heat-acclimatized", True)
cav = st.sidebar.slider("Clothing adjustment (C)", 0.0, 2.0, 0.0, 0.5,
                        help="0 = light cotton, +1 = woven coverall (ISO 7243:2017 summary). Chennai-style clothing is unmeasured.")
buffer = st.sidebar.slider("Forecast safety buffer (C)", 0.0, 4.0, 1.0, 0.5,
                           help="Added to the forecast WBGT because forecasts have error. Calibrate it with the backtest.")
st.sidebar.subheader("Work to schedule (hours)")
h_heavy = st.sidebar.number_input("Heavy (carrying, shovelling) 230 W/m2", 0.0, 8.0, 3.0, 0.5)
h_medium = st.sidebar.number_input("Medium (masonry, bar-bending) 190 W/m2", 0.0, 8.0, 3.0, 0.5)
h_light = st.sidebar.number_input("Light (supervision, finishing) 110 W/m2", 0.0, 8.0, 2.0, 0.5)

tab_plan, tab_back, tab_about = st.tabs(["Tomorrow's plan", "Backtest", "How it works"])

# ---------------- plan tab ----------------
with tab_plan:
    days = {}
    try:
        if source.startswith("Offline"):
            days = load_csv_days(str(SAMPLE_FC))
            st.info("Using SYNTHETIC sample weather (invented, for demonstration only).")
        elif source.startswith("Live"):
            days = load_live_days()
        else:
            up = st.file_uploader("Weather CSV (see README for columns)", type="csv")
            if up is not None:
                tmp = DATA / "_uploaded.csv"
                tmp.write_bytes(up.getvalue())
                days = complete_days(hourly_wbgt(read_weather_csv(tmp)))
    except Exception as e:  # network or file problems
        st.error(f"Could not load weather data: {e}")

    if not days:
        st.stop()

    dates = sorted(days)
    default = len(dates) // 2
    if source.startswith("Offline"):  # start on a typical day (median peak heat), not the hottest or coolest
        peaks = sorted(dates, key=lambda d: max(days[d].values()))
        default = dates.index(peaks[len(peaks) // 2])
    if source.startswith("Live"):
        tomorrow = dt.date.today() + dt.timedelta(days=1)
        default = dates.index(tomorrow) if tomorrow in dates else 0
    date = st.selectbox("Date", dates, index=default)
    wb = days[date]

    tasks = [Task("heavy", PRESETS["heavy"], h_heavy), Task("medium", PRESETS["medium"], h_medium),
             Task("light", PRESETS["light"], h_light)]
    plan = plan_day(wb, tasks, acclimatized, cav, buffer)

    c1, c2, c3 = st.columns(3)
    c1.metric("Peak WBGT (model)", f"{max(wb.values()):.1f} C")
    c2.metric("STOP hours", sum(1 for hp in plan.hours.values() if hp.status == "STOP"))
    req = sum(plan.requested.values())
    c3.metric("Work scheduled safely", f"{plan.total_scheduled_minutes()} of {req} min")

    refs = REF_ACCLIMATIZED if acclimatized else REF_UNACCLIMATIZED
    chart = pd.DataFrame({
        "WBGT model": {f"{h:02d}:00": v for h, v in wb.items()},
        "WBGT effective (+clothing +buffer)": {f"{h:02d}:00": hp.wbgt_eff for h, hp in plan.hours.items()},
        f"Heavy-work limit ({refs[3]:.0f})": {f"{h:02d}:00": refs[3] for h in wb},
        f"Medium-work limit ({refs[2]:.0f})": {f"{h:02d}:00": refs[2] for h in wb},
        f"Stop-all limit ({refs[1]:.0f})": {f"{h:02d}:00": refs[1] for h in wb},
    })
    st.subheader("Hourly WBGT against ISO 7243 limits")
    st.line_chart(chart)

    st.subheader("Work-rest schedule (minutes per hour)")
    table = pd.DataFrame([{"hour": f"{h:02d}:00", "WBGT eff (C)": round(hp.wbgt_eff, 1), "status": hp.status,
                           **{t.name: hp.minutes.get(t.name, 0) for t in tasks}, "rest": hp.rest_minutes}
                          for h, hp in plan.hours.items()])
    st.dataframe(table, hide_index=True)
    unmet = {k: v for k, v in plan.unmet.items() if v > 0}
    if unmet:
        st.caption("Could not be scheduled within safe limits today (minutes): " +
                   ", ".join(f"{k} {v}" for k, v in unmet.items()) +
                   ". Consider shade, cooling, more rest, or moving work to another day.")

    st.subheader("Message for the site supervisor")
    blocks = merge_blocks(hour_allowances(wb, acclimatized, cav, buffer))
    en, ta = st.columns(2)
    en.code(render_message(site, str(date), blocks, "en"), language=None)
    ta.code(render_message(site, str(date), blocks, "ta"), language=None)
    st.caption("Tamil text is a template and must be reviewed by a native speaker before real use.")

    log_text = log_to_csv_text(stoppage_log_rows(plan, str(date), site, acclimatized, cav, buffer))
    st.download_button("Download stoppage log (CSV)", log_text, file_name=f"stoppage_log_{date}.csv", mime="text/csv")

# ---------------- backtest tab ----------------
with tab_back:
    st.write("Compares fixed shifts with the planner on past days, using forecasts for planning and the "
             "archive for what actually happened.")
    fcs = sorted(p.name for p in DATA.glob("*forecast*.csv"))
    obs = sorted(p.name for p in DATA.glob("*archive*.csv"))
    real_fc = [f for f in fcs if "SYNTHETIC" not in f]
    real_ob = [f for f in obs if "SYNTHETIC" not in f]
    fc_name = st.selectbox("Forecast file", real_fc + [f for f in fcs if f not in real_fc])
    ob_name = st.selectbox("Archive file", real_ob + [f for f in obs if f not in real_ob])
    m_work = st.selectbox("Work intensity", list(PRESETS.items()), index=0, format_func=lambda kv: f"{kv[0]} ({kv[1]:.0f} W/m2)")[1]
    if st.button("Run backtest"):
        results, meta = bt.run_from_files(DATA / fc_name, DATA / ob_name, m_work=m_work,
                                          acclimatized=acclimatized, cav=cav)
        if "SYNTHETIC" in fc_name.upper() or "SYNTHETIC" in ob_name.upper():
            st.error("SYNTHETIC DATA: these numbers only test the code. They are NOT findings.")
        st.caption(f"{meta['note']} Calibrated buffer: {meta['buffer_c']:.2f} C.")
        df = pd.DataFrame([{"policy": r.name, "scheduled min": r.scheduled, "safe min": r.safe,
                            "overload min": r.overload, "safe %": round(r.safe_pct, 1),
                            "days with overload": f"{r.days_with_overload}/{r.days}",
                            "worst day overload": r.worst_day_overload} for r in results])
        st.dataframe(df, hide_index=True)
        st.bar_chart(pd.DataFrame({"safe min/day": {r.name: r.safe / r.days for r in results},
                                   "overload min/day": {r.name: r.overload / r.days for r in results}}))
        st.caption("planner_oracle uses the actual weather, so it is an upper bound that cannot be achieved in practice.")

# ---------------- about tab ----------------
with tab_about:
    st.markdown("""
**Pipeline:** Open-Meteo hourly forecast -> Liljegren outdoor WBGT -> ISO 7243 limit by work intensity ->
work fraction `f = (M_adm - 65) / (M_work - 65)` -> planner (heavy tasks into the coolest hours) ->
Tamil/English message + stoppage log.

**Not AI-scored:** the safety numbers come from a physical model and a standard. No language model writes the
safety instructions. See `docs/TECHNICAL_DESIGN.md` and `docs/ASSUMPTIONS.md`.
""")
