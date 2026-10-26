"""Weather data: read/write CSV, fetch from Open-Meteo, convert to hourly WBGT.

CSV columns (same for forecast and archive files):
    time (local ISO, e.g. 2025-04-15T09:00), temperature_2m (C), relative_humidity_2m (%),
    surface_pressure (hPa), wind_speed_10m (m/s), shortwave_radiation (W/m2),
    direct_radiation (W/m2)

Open-Meteo convention: temperature/humidity/wind are instantaneous values at the timestamp;
radiation is the AVERAGE OF THE PRECEDING HOUR. So for the work-hour block [h, h+1) we use the
mean of the values at h and h+1 for temperature/humidity/wind/pressure and the radiation
stamped h+1.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import urllib.parse
import urllib.request
from pathlib import Path

from .wbgt import cos_zenith, wbgt_liljegren

COLUMNS = ["time", "temperature_2m", "relative_humidity_2m", "surface_pressure",
           "wind_speed_10m", "shortwave_radiation", "direct_radiation"]

CHENNAI = (13.0827, 80.2707)  # latitude, longitude
WORK_HOURS = tuple(range(6, 19))  # blocks 06:00-07:00 ... 18:00-19:00

BASES = {
    "live": "https://api.open-meteo.com/v1/forecast",
    "forecast_history": "https://historical-forecast-api.open-meteo.com/v1/forecast",
    "archive": "https://archive-api.open-meteo.com/v1/archive",
}


def read_weather_csv(path) -> dict:
    """Return {datetime: {column: float}}. Rows with missing values are skipped."""
    weather = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                t = dt.datetime.fromisoformat(row["time"])
                weather[t] = {c: float(row[c]) for c in COLUMNS[1:]}
            except (ValueError, KeyError, TypeError):
                continue
    return weather


def write_weather_csv(path, weather: dict) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        for t in sorted(weather):
            w.writerow([t.strftime("%Y-%m-%dT%H:%M")] + [f"{weather[t][c]:.2f}" for c in COLUMNS[1:]])


def hourly_wbgt(weather: dict, lat: float = CHENNAI[0], lon: float = CHENNAI[1],
                tz_offset_hours: float = 5.5, hours=WORK_HOURS) -> dict:
    """Return {date: {hour: wbgt_C}} for every date that has complete data for the hour."""
    out: dict = {}
    dates = sorted({t.date() for t in weather})
    for d in dates:
        for h in hours:
            t0 = dt.datetime.combine(d, dt.time(h))
            t1 = t0 + dt.timedelta(hours=1)
            if t0 not in weather or t1 not in weather:
                continue
            a, b = weather[t0], weather[t1]
            mean = lambda k: (a[k] + b[k]) / 2.0
            mid_local = t0 + dt.timedelta(minutes=30)
            mid_utc = mid_local - dt.timedelta(hours=tz_offset_hours)
            cz = cos_zenith(lat, lon, mid_utc)
            w = wbgt_liljegren(mean("temperature_2m"), mean("relative_humidity_2m"),
                               mean("surface_pressure"), mean("wind_speed_10m"),
                               b["shortwave_radiation"], b["direct_radiation"], cz)
            out.setdefault(d, {})[h] = w
    return out


def complete_days(wbgt_by_date: dict, hours=WORK_HOURS) -> dict:
    """Keep only dates that have every work-hour block."""
    return {d: v for d, v in wbgt_by_date.items() if all(h in v for h in hours)}


def fetch_open_meteo(kind: str, start: str | None = None, end: str | None = None,
                     lat: float = CHENNAI[0], lon: float = CHENNAI[1], timeout: int = 60) -> dict:
    """Download hourly weather and return it in the same {datetime: {col: float}} format.

    kind: 'live' (next days' forecast), 'forecast_history' (past forecasts), 'archive' (ERA5 proxy)
    start/end: 'YYYY-MM-DD' (not used for 'live').
    """
    if kind not in BASES:
        raise ValueError(f"kind must be one of {list(BASES)}")
    params = {"latitude": lat, "longitude": lon, "hourly": ",".join(COLUMNS[1:]),
              "wind_speed_unit": "ms", "timezone": "Asia/Kolkata"}
    if kind == "live":
        params["forecast_days"] = 3
    else:
        if not (start and end):
            raise ValueError("start and end dates are required")
        params["start_date"], params["end_date"] = start, end
    url = BASES[kind] + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        payload = json.load(resp)
    hourly = payload["hourly"]
    weather = {}
    for i, ts in enumerate(hourly["time"]):
        try:
            weather[dt.datetime.fromisoformat(ts)] = {c: float(hourly[c][i]) for c in COLUMNS[1:]}
        except (TypeError, ValueError):
            continue  # null value from the API
    return weather
