"""Geometria lunar para estimar dimensões de uma cratera sem usar nomes.

A medida usa somente as coordenadas de dois pontos escolhidos pelo visitante,
considerados como bordas opostas. Modelo esférico com raio de referência
de 1737,4 km. Não é altimetria nem detecção automática de borda.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import asin, atan2, cos, degrees, hypot, isfinite, pi, radians, sin, sqrt

MOON_RADIUS_KM = 1737.4
NASA_MOON_FACT_SHEET = "https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html"


def validate_point(point: tuple[float, float]) -> tuple[float, float]:
    latitude, longitude = float(point[0]), float(point[1])
    if not (isfinite(latitude) and isfinite(longitude)):
        raise ValueError("As coordenadas precisam ser números finitos.")
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("Latitude deve estar entre -90° e 90° e longitude entre -180° e 180°.")
    return latitude, longitude


def great_circle_distance_km(
    point_a: tuple[float, float], point_b: tuple[float, float],
    radius_km: float = MOON_RADIUS_KM,
) -> float:
    """Arco menor sobre a esfera lunar (fórmula de haversine)."""
    a_lat, a_lon = validate_point(point_a)
    b_lat, b_lon = validate_point(point_b)
    if not isfinite(radius_km) or radius_km <= 0:
        raise ValueError("O raio do corpo deve ser positivo.")
    phi1, phi2 = radians(a_lat), radians(b_lat)
    dphi = phi2 - phi1
    dlambda = radians((b_lon - a_lon + 180.0) % 360.0 - 180.0)
    h = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    return 2 * radius_km * asin(min(1.0, sqrt(max(0.0, h))))


def spherical_midpoint(
    point_a: tuple[float, float], point_b: tuple[float, float],
) -> tuple[float, float]:
    """Ponto central aproximado na esfera; indefinido se forem antipodais."""
    lat1, lon1 = map(radians, validate_point(point_a))
    lat2, lon2 = map(radians, validate_point(point_b))
    x = cos(lat1) * cos(lon1) + cos(lat2) * cos(lon2)
    y = cos(lat1) * sin(lon1) + cos(lat2) * sin(lon2)
    z = sin(lat1) + sin(lat2)
    norm = sqrt(x*x + y*y + z*z)
    if norm < 1e-10:
        raise ValueError("Não há um ponto médio único para pontos opostos na Lua.")
    latitude = degrees(asin(max(-1.0, min(1.0, z/norm))))
    longitude = (degrees(atan2(y,x)) + 180.0) % 360.0 - 180.0
    return latitude, longitude


@dataclass(frozen=True)
class CraterEstimate:
    diameter_km: float
    radius_km: float
    area_km2: float
    separation_deg: float
    midpoint: tuple[float, float]


def estimate_crater(
    point_a: tuple[float, float], point_b: tuple[float, float],
) -> CraterEstimate:
    """Comprimento geográfico AB como diâmetro hipotético + área de disco ideal."""
    distance = great_circle_distance_km(point_a, point_b)
    if distance < 0.001:
        raise ValueError("Selecione duas bordas diferentes para efetuar a medição.")
    midpoint = spherical_midpoint(point_a, point_b)
    return CraterEstimate(
        diameter_km=distance,
        radius_km=distance/2,
        area_km2=pi*(distance/2)**2,
        separation_deg=degrees(distance/MOON_RADIUS_KM),
        midpoint=midpoint,
    )
