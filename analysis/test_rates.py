"""Validation of the clock-rate model against published values only."""

import math

import pytest

import rates as r


def test_gps_net_rate_matches_ashby_eq35():
    # Ashby 2003, Eq. 35, p. 16: -4.4647e-10 = +2.5046e-10 - 6.9693e-10 (correction = minus offset).
    assert r.orbit_rate(r.GM_EARTH, r.A_GPS) == pytest.approx(-2.5046e-10, abs=5e-15)
    assert r.geoid_rate() == pytest.approx(-6.9693e-10, abs=5e-15)
    assert r.gps_vs_geoid() == pytest.approx(4.4647e-10, abs=5e-15)


def test_moon_surface_matches_ashby_patla_2024():
    # Ashby & Patla 2024: a clock near the Moon's equator gains 56.02 us/day on one near Earth's.
    # Our model omits solar tidal terms, hence the 0.1 us/day tolerance.
    assert r.per_day(r.moon_surface_rate() - r.geoid_rate()) == pytest.approx(56.02, abs=0.1)


def test_mars_surface_matches_ashby_patla_2025_mean():
    # Ashby & Patla 2025: 477 us/day on average, varying by up to 226 us/day over a Mars year.
    # Our circular-orbit model omits eccentricity and third bodies, hence the 20 us/day tolerance.
    frac = r.mars_surface_rate_helio() - r.earth_surface_rate_helio()
    assert r.per_day(frac) == pytest.approx(477, abs=20)


def test_survey_magnitudes_table_is_consistent():
    # paper/main.typ, tab:magnitudes: LEO time dilation ~3e-10; Earth orbital speed beta ~1e-4.
    v_leo = r.circular_speed(r.GM_EARTH, r.R_EARTH + 400e3)
    assert (v_leo / r.C) ** 2 / 2 == pytest.approx(3e-10, rel=0.15)
    assert r.circular_speed(r.GM_SUN, r.AU) / r.C == pytest.approx(1e-4, rel=0.01)


def test_geometry_ground_leo():
    station = r.Circle(r.R_EARTH, r.OMEGA_EARTH)
    leo = r.Circle(r.R_EARTH + 400e3, r.circular_speed(r.GM_EARTH, r.R_EARTH + 400e3) / (r.R_EARTH + 400e3))
    d_min, d_max, _ = r.range_stats(station, leo, lambda t: r.above_horizon(station, leo, t))
    assert d_min == pytest.approx(400e3, abs=1e3)
    assert d_max == pytest.approx(math.sqrt((r.R_EARTH + 400e3) ** 2 - r.R_EARTH ** 2), abs=1e3)


def test_geometry_corotating_stations_have_no_range_rate():
    a = r.Circle(r.R_EARTH, r.OMEGA_EARTH, 0.0)
    b = r.Circle(r.R_EARTH, r.OMEGA_EARTH, 0.157)
    _, _, rr = r.range_stats(a, b, samples=1000)
    assert rr < 1e-6


def test_geometry_earth_mars_closest_approach():
    d_min, d_max, _ = r.range_stats(r.Circle(r.AU, 1.991e-7), r.Circle(r.A_MARS, 1.059e-7))
    assert d_min == pytest.approx(r.A_MARS - r.AU, rel=1e-4)
    assert d_max == pytest.approx(r.A_MARS + r.AU, rel=1e-4)
