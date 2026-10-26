# Heat-Safe Shift Planner

**Team:** [ADD YOUR ACTUAL TEAM NAME] · Hack for Social Cause (VBYLD 2027) · **Registration ID:** [VERIFY IN PORTAL]
Theme: AI, GIS & Emerging Technologies (climate resilience) · SDG 3, 8, 13 · State: Tamil Nadu

> Construction workers in Tamil Nadu follow fixed shifts in humid heat. Official guidance is a one-size
> 12-3 pm advisory. This tool tells a site supervisor, the evening before, **when to work, slow down or stop**,
> using a physical heat-stress model and ISO 7243 limits, and keeps an auditable log of every decision.

**Not an AI score.** The safety numbers come from a published physical model (Liljegren WBGT) and a standard
(ISO 7243). No language model writes or changes the safety instructions; messages come from fixed templates.

## What it does
1. Takes an hourly weather forecast for the site (Open-Meteo, free) or a CSV.
2. Computes outdoor **WBGT** each hour (Liljegren model via `thermofeel`).
3. Applies **ISO 7243** limits for the work intensity, acclimatization and clothing.
4. Plans minutes of work per hour for each task: heaviest work in the coolest hours.
5. Produces a Tamil/English supervisor message and a **stoppage log** (CSV) showing inputs, limit and decision.
6. **Backtests** the planner against fixed shifts (9-6 and a 12-3 break) on past days.

## Quick start (about 5 minutes)
```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate        Mac/Linux:  source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q                       # all tests should pass
python -m heatplanner.cli plan            # plan for a sample day (offline)
streamlit run app.py                      # interactive demo in the browser
```
No API keys and no environment variables are needed. Optional: pass `--lat/--lon` to change the site location.

## Use real weather data
```bash
python -m heatplanner.cli fetch --start 2025-04-01 --end 2025-05-31
python -m heatplanner.cli backtest \
  --forecast data/chennai_forecast_2025-04-01_2025-05-31.csv \
  --archive  data/chennai_archive_2025-04-01_2025-05-31.csv --label chennai_apr_may_2025
python -m heatplanner.cli plan --live --site "My site"     # tomorrow's live forecast (internet)
```

### Weather CSV format
`time, temperature_2m (C), relative_humidity_2m (%), surface_pressure (hPa), wind_speed_10m (m/s), shortwave_radiation (W/m2), direct_radiation (W/m2)` with hourly local timestamps (see `data/sample_*_SYNTHETIC.csv`).

## Results
> Fill this in after running the backtest on REAL data (see above). Numbers from the bundled sample are **synthetic
> and are not findings**.

| Policy | Scheduled min | Safe min | Overload min | Safe % | Days with overload |
|---|---|---|---|---|---|
| status_quo_9_to_6 | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN |
| blanket_12_to_3 | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN |
| planner_no_buffer | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN |
| planner_buffered | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN |
| planner_oracle (upper bound) | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN |

**Real-data evaluation pending.** Do not report performance claims until the forecast-history and archive downloads complete and the generated CSV is reviewed. Record period, Chennai coordinates, task intensity, evaluation-day count and calibrated buffer alongside the results.

## Project layout
```
heatplanner/   limits.py (ISO limits)  wbgt.py (Liljegren)  data.py  planner.py  messages.py  backtest.py  cli.py
app.py         Streamlit demo
tests/         automated tests (pytest; verify locally after installing dependencies)
data/          SYNTHETIC sample weather (for offline demo/tests only)
docs/          TECHNICAL_DESIGN.md  ASSUMPTIONS.md  AI_USAGE.md  DEMO_VIDEO_SCRIPT.md
scripts/       make_sample_data.py
```

## Honest limitations
- WBGT comes from forecast/reanalysis data, not a site sensor. Gridded WBGT is minimally validated against ground
  observations; we add a forecast-error buffer and plan an on-site sensor check.
- The "actual weather" in the backtest is an ERA5 reanalysis proxy, not worker-level measurements.
- ISO 7243 values were taken from secondary summaries and must be checked against the standard.
- Task-to-intensity presets (heavy 230, medium 190, light 110 W/m2) and the clothing adjustment are assumptions.
- The Tamil text needs native-speaker and safety-officer review. No real SMS/WhatsApp sending is implemented.
- Not a medical device or a compliance certificate; a safety officer must stay in the loop.

## Data and credits
Weather data: [Open-Meteo.com](https://open-meteo.com/) (attribution required; check their terms for your use).
WBGT: Liljegren et al. (2008) via [thermofeel](https://github.com/ecmwf/thermofeel). See `docs/ASSUMPTIONS.md` for sources.

## License
MIT, see `LICENSE`. AI-assistance disclosure: `docs/AI_USAGE.md`.
