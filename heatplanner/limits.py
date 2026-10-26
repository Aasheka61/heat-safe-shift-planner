"""WBGT limits and work-rest fractions based on ISO 7243 reference values.

All numbers are documented in docs/ASSUMPTIONS.md. The reference values were taken from
secondary sources (ISO 7243 summaries) and MUST be checked against the standard text.

Key idea
--------
ISO 7243 gives a maximum WBGT for each metabolic-rate class. If the (effective) WBGT is
higher than the limit for the work being done, work must be reduced. We use the
time-weighted approach: work minutes per hour are chosen so that the *average* metabolic
rate over the hour (work + rest at 65 W/m2) stays at or below the highest class that the
current WBGT allows.

    f = (M_admissible - M_rest) / (M_work - M_rest),  clamped to 0..1
"""
from __future__ import annotations

import math

M_REST = 65.0  # W/m2, top of metabolic class 0 (resting)

# Upper bound of each metabolic class, W/m2:  class 0, 1, 2, 3
CLASS_UPPER = (65.0, 130.0, 200.0, 260.0)

# Reference WBGT (deg C) per class. Class 3 uses the conservative "no air movement" value.
REF_ACCLIMATIZED = (33.0, 30.0, 28.0, 25.0)
REF_UNACCLIMATIZED = (32.0, 29.0, 26.0, 22.0)

# Task presets (W/m2). ASSUMPTION: Chennai construction work was measured at 170-220 W/m2
# (Venugopal et al. 2014). Mapping tasks to these presets must be confirmed with supervisors.
PRESETS = {"heavy": 230.0, "medium": 190.0, "light": 110.0}


def _refs(acclimatized: bool) -> tuple:
    return REF_ACCLIMATIZED if acclimatized else REF_UNACCLIMATIZED


def metabolic_class(m_work: float) -> int:
    """Return ISO metabolic class 0-3 for a work intensity in W/m2."""
    for cls, upper in enumerate(CLASS_UPPER):
        if m_work <= upper:
            return cls
    raise ValueError("Intensity above 260 W/m2 (class 4) is not supported in this prototype.")


def reference_wbgt(m_work: float, acclimatized: bool = True) -> float:
    """WBGT limit (deg C) for continuous work at this intensity."""
    return _refs(acclimatized)[metabolic_class(m_work)]


def admissible_metabolic_rate(wbgt_eff: float, acclimatized: bool = True) -> float:
    """Highest average metabolic rate (W/m2) allowed at this effective WBGT."""
    refs = _refs(acclimatized)
    for cls in (3, 2, 1, 0):
        if wbgt_eff <= refs[cls]:
            return CLASS_UPPER[cls]
    return M_REST  # above the class-0 limit: rest and cool down only


def work_fraction(m_work: float, wbgt_eff: float, acclimatized: bool = True) -> float:
    """Fraction (0..1) of each hour that can be spent working at m_work."""
    if m_work <= M_REST:
        return 1.0
    m_adm = admissible_metabolic_rate(wbgt_eff, acclimatized)
    f = (m_adm - M_REST) / (m_work - M_REST)
    return max(0.0, min(1.0, f))


def allowed_minutes(m_work: float, wbgt_eff: float, acclimatized: bool = True, step: int = 5) -> int:
    """Allowed work minutes per hour, rounded DOWN to a multiple of `step` (safe side)."""
    f = work_fraction(m_work, wbgt_eff, acclimatized)
    return int(math.floor(60.0 * f / step + 1e-9)) * step


def limit_description(wbgt_eff: float, acclimatized: bool = True) -> str:
    """Human-readable explanation of which limit applied (used in the stoppage log)."""
    refs = _refs(acclimatized)
    for cls in (3, 2, 1, 0):
        if wbgt_eff <= refs[cls]:
            return f"WBGT_eff {wbgt_eff:.1f} <= class-{cls} limit {refs[cls]:.0f} C: max avg metabolic rate {CLASS_UPPER[cls]:.0f} W/m2"
    return f"WBGT_eff {wbgt_eff:.1f} > class-0 limit {refs[0]:.0f} C: stop work, rest and cool down"


def status(wbgt_eff: float, acclimatized: bool = True) -> str:
    """NORMAL (heavy work unrestricted), LIMITED (some work reduced) or STOP (no work)."""
    if admissible_metabolic_rate(wbgt_eff, acclimatized) <= M_REST:
        return "STOP"
    if allowed_minutes(PRESETS["heavy"], wbgt_eff, acclimatized) >= 60:
        return "NORMAL"
    return "LIMITED"
