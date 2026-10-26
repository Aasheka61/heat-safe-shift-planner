import pytest

from heatplanner.limits import (PRESETS, admissible_metabolic_rate, allowed_minutes, metabolic_class,
                                reference_wbgt, status, work_fraction)


def test_reference_values_acclimatized():
    assert reference_wbgt(60) == 33
    assert reference_wbgt(110) == 30
    assert reference_wbgt(190) == 28
    assert reference_wbgt(230) == 25


def test_reference_values_unacclimatized_are_lower():
    for m in (60, 110, 190, 230):
        assert reference_wbgt(m, acclimatized=False) < reference_wbgt(m, acclimatized=True)


def test_class_above_260_not_supported():
    with pytest.raises(ValueError):
        metabolic_class(300)


def test_full_work_below_limit():
    assert work_fraction(230, 24.9) == 1.0
    assert allowed_minutes(230, 24.9) == 60


def test_work_fraction_never_increases_with_heat():
    fractions = [work_fraction(230, w / 2) for w in range(40, 72)]
    assert all(a >= b for a, b in zip(fractions, fractions[1:]))


def test_known_values_heavy_work():
    # M_adm 200 -> (200-65)/(230-65) = 0.818 -> 49 min -> rounded down to 45
    assert allowed_minutes(230, 27.0) == 45
    # M_adm 130 -> 65/165 = 0.394 -> 23 min -> 20
    assert allowed_minutes(230, 29.0) == 20


def test_stop_above_30_for_work():
    assert allowed_minutes(230, 30.5) == 0
    assert allowed_minutes(110, 30.5) == 0
    assert admissible_metabolic_rate(35.0) == 65.0


def test_light_work_allowed_up_to_30():
    assert allowed_minutes(PRESETS["light"], 30.0) == 60


def test_minutes_are_multiples_of_five_and_rounded_down():
    for w in [x / 4 for x in range(80, 140)]:
        m = allowed_minutes(230, w)
        assert m % 5 == 0
        assert m <= 60 * work_fraction(230, w) + 1e-6


def test_status_labels():
    assert status(24.0) == "NORMAL"
    assert status(27.0) == "LIMITED"
    assert status(31.0) == "STOP"
