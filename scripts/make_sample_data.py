"""Create SYNTHETIC weather files so the prototype runs offline.

!!! These numbers are invented to look like a Chennai April-May. They are for testing the
code and demonstrating the interface ONLY. Never present results from them as findings.
Real data: python -m heatplanner.cli fetch --start 2025-04-01 --end 2025-05-31
"""
import datetime as dt
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from heatplanner.data import write_weather_csv  # noqa: E402
from heatplanner.wbgt import cos_zenith  # noqa: E402

random.seed(42)
LAT, LON = 13.0827, 80.2707
START, DAYS = dt.date(2025, 4, 15), 30


def archive_hour(d, h, tmin, tmax, cloud, rh_base):
    mean, amp = (tmax + tmin) / 2, (tmax - tmin) / 2
    import math
    temp = mean + amp * math.cos(2 * math.pi * (h - 15) / 24)
    frac = (temp - tmin) / (tmax - tmin)
    rh = max(35.0, min(98.0, rh_base - 38 * frac + random.gauss(0, 2)))
    wind = max(0.6, 1.8 + (1.6 if 12 <= h <= 19 else 0.0) + random.gauss(0, 0.4))
    pres = 1006.0 - 1.5 * math.cos(2 * math.pi * (h - 4) / 12) + random.gauss(0, 0.2)
    mid = dt.datetime.combine(d, dt.time(h)) - dt.timedelta(minutes=30, hours=5.5)
    cz = max(0.0, cos_zenith(LAT, LON, mid))
    ghi = 1000.0 * (cz ** 1.15) * cloud
    direct = ghi * max(0.0, min(0.85, 1.15 * cloud - 0.3))
    return {"temperature_2m": temp, "relative_humidity_2m": rh, "surface_pressure": pres,
            "wind_speed_10m": wind, "shortwave_radiation": ghi, "direct_radiation": direct}


archive, forecast = {}, {}
for i in range(DAYS):
    d = START + dt.timedelta(days=i)
    tmax, tmin = random.gauss(35.0, 2.2), random.gauss(27.5, 1.0)
    cloud, rh_base = random.uniform(0.40, 1.0), random.gauss(78, 6)
    for h in range(24):
        t = dt.datetime.combine(d, dt.time(h))
        a = archive_hour(d, h, tmin, tmax, cloud, rh_base)
        archive[t] = a
        forecast[t] = {
            "temperature_2m": a["temperature_2m"] + 0.3 + random.gauss(0, 1.0),
            "relative_humidity_2m": max(30.0, min(99.0, a["relative_humidity_2m"] + random.gauss(0, 6))),
            "surface_pressure": a["surface_pressure"] + random.gauss(0, 0.5),
            "wind_speed_10m": max(0.5, a["wind_speed_10m"] + random.gauss(0, 0.7)),
            "shortwave_radiation": max(0.0, a["shortwave_radiation"] * random.lognormvariate(0, 0.2)),
            "direct_radiation": max(0.0, a["direct_radiation"] * random.lognormvariate(0, 0.25)),
        }
out = Path(__file__).resolve().parent.parent / "data"
write_weather_csv(out / "sample_archive_SYNTHETIC.csv", archive)
write_weather_csv(out / "sample_forecast_SYNTHETIC.csv", forecast)
print("wrote", out / "sample_archive_SYNTHETIC.csv", "and", out / "sample_forecast_SYNTHETIC.csv")
