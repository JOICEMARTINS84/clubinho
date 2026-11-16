"""Testes offline da geometria da medição de crateras lunares."""
import math

import pytest

from crater_measure import (
    MOON_RADIUS_KM, great_circle_distance_km,
    spherical_midpoint, estimate_crater, validate_point,
)


def test_same_latitude_one_degree_arc_matches_nasa_reference_radius():
    distance = great_circle_distance_km((0, 0), (0, 1))
    assert distance == pytest.approx(MOON_RADIUS_KM * math.pi / 180, abs=1e-8)


def test_two_edges_give_circular_area_from_diameter():
    result = estimate_crater((0, 0), (0, 2))
    assert result.diameter_km == pytest.approx(MOON_RADIUS_KM * math.pi / 90, rel=1e-10)
    assert result.radius_km == pytest.approx(result.diameter_km / 2)
    assert result.area_km2 == pytest.approx(math.pi * result.radius_km**2)
    assert result.midpoint[0] == pytest.approx(0)
    assert result.midpoint[1] == pytest.approx(1)


def test_antimeridian_wrap_short_arc_not_long_way_around():
    distance = great_circle_distance_km((0, 179.9), (0, -179.9))
    assert distance == pytest.approx(MOON_RADIUS_KM * math.radians(0.2), rel=1e-9)
    midpoint = spherical_midpoint((0, 179.9), (0, -179.9))
    assert midpoint[0] == pytest.approx(0)
    assert abs(abs(midpoint[1]) - 180) < 1e-6


def test_symmetry_of_distances_and_polar_longitudes():
    a, b = (85.0, 40.0), (85.0, 60.0)
    assert great_circle_distance_km(a, b) == pytest.approx(
        great_circle_distance_km(b, a)
    )
    assert great_circle_distance_km((90, 0), (90, 160)) < 1e-6


def test_duplicate_points_rejected_for_diameter():
    with pytest.raises(ValueError, match="bordas diferentes"):
        estimate_crater((-43.3, -11.22), (-43.3, -11.22))


def test_antipodal_points_have_undefined_midpoint():
    with pytest.raises(ValueError, match="ponto médio único"):
        estimate_crater((0, 0), (0, 180))


@pytest.mark.parametrize("p", [(91, 0), (0, 181), (float("nan"), 0), (0, float("inf"))])
def test_bad_coordinates_not_allowed(p):
    with pytest.raises(ValueError):
        validate_point(p)


def test_one_kilometre_in_real_moon_coordinates():
    delta_lon = math.degrees(1.0 / MOON_RADIUS_KM)
    result = estimate_crater((0, -delta_lon/2), (0, delta_lon/2))
    assert result.diameter_km == pytest.approx(1.0, rel=1e-10)
    assert result.area_km2 == pytest.approx(math.pi/4, rel=1e-10)
