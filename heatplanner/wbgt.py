"""Outdoor WBGT from weather variables using the Liljegren model (via the thermofeel package).

Why not the simple formula 0.567*Ta + 0.393*e + 3.94?  A published evaluation found it greatly
overestimates heat stress in hot-humid regions (like Chennai) and recommends discontinuing it.
"""
from __future__ import annotations

import datetime as dt
import math

import numpy as np
import thermofeel as tf


def cos_zenith(lat: float, lon: float, when_utc: dt.datetime) -> float:
    """Cosine of the solar zenith angle (NOAA low-precision solar position)."""
    doy = when_utc.timetuple().tm_yday
    g = 2 * math.pi / 365 * (doy - 1 + (when_utc.hour - 12) / 24)
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g)
            - 0.006758 * math.cos(2 * g) + 0.000907 * math.sin(2 * g)
            - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                    - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    minutes = when_utc.hour * 60 + when_utc.minute + when_utc.second / 60
    hour_angle = math.radians((minutes + eqt + 4 * lon) / 4 - 180)
    la = math.radians(lat)
    return math.sin(la) * math.sin(decl) + math.cos(la) * math.cos(decl) * math.cos(hour_angle)


def wbgt_liljegren(temp_c: float, rh_pct: float, pressure_hpa: float, wind10_ms: float,
                   ghi_wm2: float, direct_horizontal_wm2: float, cossza: float) -> float:
    """Outdoor WBGT in deg C (Liljegren et al. 2008, thermofeel implementation)."""
    ghi = max(0.0, float(ghi_wm2))
    if cossza <= 0.0:
        ghi = 0.0
    fdir = 0.0 if ghi <= 0.0 else min(0.9, max(0.0, float(direct_horizontal_wm2)) / ghi)
    rh = min(100.0, max(1.0, float(rh_pct)))

    def arr(x):
        return np.array([x], dtype=float)

    out = tf.calculate_wbgt_liljegren(arr(temp_c + 273.15), arr(rh), arr(pressure_hpa),
                                      arr(max(0.0, wind10_ms)), arr(ghi), arr(fdir), arr(cossza))
    return float(out[0]) - 273.15
