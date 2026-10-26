# Heat-Safe Shift Planner

**A weather-based heat-safety planning tool for outdoor workers**

A prototype designed to help supervisors plan outdoor work during hot weather by estimating Wet-Bulb Globe Temperature (WBGT), applying configurable work-rest limits, and prioritising work during comparatively cooler hours.

**Team Name:** Pirates  
**Team Lead:** Amirtha V.  
**Team Member:** Aasheka E.  
**Registration ID:** HSC|TN|01643  
**Theme:** AI, GIS & Emerging Technologies — Climate Resilience  
**SDGs:** SDG 3 — Good Health and Well-being; SDG 8 — Decent Work and Economic Growth; SDG 13 — Climate Action  
**Target Region:** Tamil Nadu, India

**GitHub Repository:** https://github.com/Aasheka61/heat-safe-shift-planner

---

## 1. Problem Statement

Outdoor workers such as construction workers, street vendors, delivery workers and other people working under direct sunlight can face dangerous heat exposure. Fixed work schedules and generic midday breaks may not adequately account for changing weather conditions throughout the day.

Supervisors need a practical way to identify comparatively safer working hours, plan tasks according to their intensity, and communicate heat-related precautions clearly.

Heat-Safe Shift Planner explores how weather data and heat-stress modelling can support more informed outdoor work scheduling.

## 2. Proposed Solution

Heat-Safe Shift Planner is a Python-based prototype that analyses hourly weather data and produces a heat-aware work schedule.

The prototype:

- Retrieves weather forecast and historical archive data through Open-Meteo.
- Accepts hourly weather data from CSV files.
- Estimates WBGT using the Liljegren method implemented through the `thermofeel` library.
- Applies configured heat-exposure limits based on work intensity, acclimatisation and clothing assumptions.
- Prioritises tasks during comparatively cooler hours, considering task intensity.
- Generates English and Tamil supervisor messages.
- Produces a stoppage-log CSV to support review of planned work restrictions.
- Compares the planner with fixed-shift policies using a historical-weather backtest.

The tool is intended to support decision-making, not replace qualified occupational-safety professionals, on-site measurements or official safety procedures.

## 3. How It Works

1. **Weather data input:** Load hourly forecast data or a compatible CSV file.
2. **Heat-stress estimation:** Calculate model-based WBGT values from the available meteorological inputs.
3. **Work-limit assessment:** Compare estimated heat stress with the configured limits and task assumptions.
4. **Schedule planning:** Prioritise higher-intensity tasks during comparatively cooler eligible hours.
5. **Safety communication:** Generate supervisor messages and a stoppage log.
6. **Evaluation:** Compare planned schedules with fixed-shift alternatives using historical archive weather.

## 4. Technology Stack

- **Programming language:** Python
- **Weather data:** Open-Meteo forecast and historical archive data
- **Heat-stress modelling:** `thermofeel` and the Liljegren WBGT method
- **Data processing:** Python data-processing libraries
- **Testing:** `pytest`
- **Outputs:** CSV reports and a backtest chart

The prototype uses a physics-based heat-stress calculation and configured rules for planning. It does not claim that an AI-generated safety score independently establishes whether working conditions are safe.

## 5. Requirements

- Python installed on your computer
- Git, if you want to clone the repository
- VS Code or another Python-compatible editor (optional)

Install the dependencies listed in `requirements.txt`. The project does not require an API key for the documented Open-Meteo workflow.

## 6. Installation and Setup

### Step 1: Clone the repository

```bash
git clone https://github.com/Aasheka61/heat-safe-shift-planner.git
cd heat-safe-shift-planner
```

Alternatively, download the repository as a ZIP file from GitHub and extract it.

### Step 2: Create a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
```

If environment creation fails, resolve the Python installation or virtual-environment issue before continuing.

### Step 3: Activate the environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use an approved environment-activation method for your system rather than changing security settings unnecessarily.

### Step 4: Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### Step 5: Run the tests

```powershell
python -m pytest -q
```

**Development test result:** 28 tests passed in the tested project environment. Results may vary if dependencies or code are changed.

## 7. Running the Prototype

Run these commands from the project root with the virtual environment activated.

### A. Generate a sample plan

```powershell
python -m heatplanner.cli plan
```

The sample workflow uses the project's synthetic sample forecast. Its output demonstrates how the planner operates; it must not be interpreted as a real-world heat-safety assessment.

### B. View the command options

```powershell
python -m heatplanner.cli --help
```

The available command groups include `plan`, `backtest` and `fetch`.

### C. Fetch weather data

The following command retrieves data for the specified date range:

```powershell
python -m heatplanner.cli fetch --start 2025-04-01 --end 2025-05-31
```

The tested workflow saved these files:

- `data/chennai_forecast_2025-04-01_2025-05-31.csv`
- `data/chennai_archive_2025-04-01_2025-05-31.csv`

The archive data is a reanalysis-based proxy. It is not a record of individual workers' heat exposure or measurements from a particular worksite.

### D. Run the historical backtest

```powershell
python -m heatplanner.cli backtest --forecast data/chennai_forecast_2025-04-01_2025-05-31.csv --archive data/chennai_archive_2025-04-01_2025-05-31.csv --label chennai_apr_may_2025
```

The tested run generated:

- `outputs/chennai_apr_may_2025_summary.csv`
- `outputs/chennai_apr_may_2025_chart.png`

These are generated outputs. They will be available in a fresh clone only if they have also been committed to the repository or generated by running the relevant commands.

## 8. Preliminary Historical-Weather Results

**Location:** Chennai, Tamil Nadu  
**Period:** 1 April–31 May 2025  
**Evaluation method:** 30 days for forecast-error calibration, followed by 31 days for evaluation.

The following results came from a completed prototype backtest using Open-Meteo historical forecast data and archive reanalysis data.

| Policy | Scheduled minutes | Model-compliant minutes | Overload minutes | Safe-minute percentage | Days with overload |
|---|---:|---:|---:|---:|---:|
| Fixed shift, 9 AM–6 PM | 14,880 | 2,315 | 12,565 | 15.6% | 31/31 |
| Fixed shift with 12 PM–3 PM break | 14,880 | 2,980 | 11,900 | 20.0% | 31/31 |
| Planner without buffer | 5,275 | 5,275 | 0 | 100.0% | 0/31 |
| Planner with calibrated buffer | 5,275 | 5,275 | 0 | 100.0% | 0/31 |
| Archive-informed oracle comparison | 5,275 | 5,275 | 0 | 100.0% | 0/31 |

**Forecast-error calibration:** The selected buffer was 0.00°C using the configured 90th-percentile calibration method. This result means the selected percentile of the calibration errors did not produce a positive buffer; it does not mean that forecasts never underestimate heat stress.

### Interpretation

The planner scheduled 5,275 work minutes during the evaluation period, compared with 14,880 minutes for each fixed-shift policy. Its 100% model-compliant-minute score therefore reflects a more restrictive schedule, not equivalent work output with zero risk.

The archive-informed oracle uses archive weather when making scheduling decisions. It is an upper-bound comparison, not a deployable forecast-based policy.

These results are preliminary model-based results, not validated occupational-safety findings. The archive data is a reanalysis proxy rather than worker-level or on-site sensor measurements. The WBGT implementation, hourly radiation assumptions, ISO 7243 thresholds, task-intensity presets and forecast-error calibration require further verification before operational use.

## 9. Limitations and Safety Considerations

- **Model estimates are not direct measurements:** Estimated WBGT may differ from conditions at a particular worksite.
- **Weather data has limitations:** Historical archive data does not capture each worker's actual exposure, hydration, health, clothing, workload or local microclimate.
- **Safety thresholds require verification:** Configured work-rest limits and task-intensity assumptions must be checked against applicable standards and qualified occupational-safety guidance.
- **Scheduling is heuristic:** The current planner prioritises tasks using a rule-based approach. Its scheduling method has not been established as an independently validated occupational-safety method.
- **Zero overload is not zero risk:** A schedule with no model-calculated overload minutes does not guarantee safe working conditions.
- **Operational use requires validation:** Field testing, appropriate on-site measurements, expert review and worker feedback are necessary before the tool can inform actual workplace decisions.

When actual conditions conflict with a generated schedule, applicable safety procedures and qualified safety personnel must take precedence.

## 10. Future Improvements

- Validate the WBGT calculations and work-rest thresholds against authoritative occupational-safety guidance.
- Compare model estimates with suitable on-site weather and heat-stress measurements.
- Evaluate performance across additional locations, seasons and weather conditions.
- Improve task scheduling using worker feedback, workload constraints and validated occupational-safety rules.
- Add clearer visualisations of hourly heat stress and work-rest recommendations.
- Improve Tamil and English communication for supervisors and outdoor workers.
- Develop a user-friendly interface for entering site information and reviewing schedules.
- Evaluate forecast uncertainty and conservative safety margins using more extensive out-of-sample data.

## 11. Project Structure

The main project components include:

- `heatplanner/cli.py` — command-line interface for planning, fetching and backtesting.
- `heatplanner/data.py` — weather-data handling and preparation.
- `heatplanner/wbgt.py` — WBGT calculation.
- `heatplanner/limits.py` — configured heat-exposure limits and task assumptions.
- `heatplanner/planner.py` — work-scheduling logic.
- `heatplanner/backtest.py` — historical evaluation and comparison of policies.
- `data/` — sample and retrieved weather datasets.
- `outputs/` — generated reports and charts.
- `requirements.txt` — Python dependencies.
- `sample_forecast_SYNTHETIC.csv` — synthetic demonstration data, where included in the repository.
- `README.md` — project documentation.

Some generated files may be created locally rather than tracked by Git. The exact files available in a fresh clone depend on what has been committed to the repository.

## 12. Social Impact

Heat-Safe Shift Planner explores a practical application of weather data and computational heat-stress modelling to a growing climate-resilience challenge.

The project aims to support:

- **SDG 3 — Good Health and Well-being:** Better awareness of occupational heat exposure.
- **SDG 8 — Decent Work and Economic Growth:** More informed planning for outdoor work.
- **SDG 13 — Climate Action:** Exploring data-driven adaptation to extreme heat.

The intended beneficiaries include construction workers, street vendors, delivery workers and other people whose work requires prolonged outdoor exposure.

The prototype is a starting point for research and validation, rather than a certified safety system.

## 13. Team

**Team Name:** Pirates

- **Team Lead:** Amirtha V.
- **Team Member:** Aasheka E.

**Registration ID:** HSC|TN|01643

**Project:** Heat-Safe Shift Planner  
**Region:** Tamil Nadu, India  
**Theme:** AI, GIS & Emerging Technologies — Climate Resilience

---

*Disclaimer: This project is a prototype for educational and evaluation purposes. It does not replace official weather alerts, on-site WBGT measurements, applicable occupational-safety standards or professional safety advice.*