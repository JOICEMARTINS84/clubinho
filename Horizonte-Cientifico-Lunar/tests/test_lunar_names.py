"""Testes offline: KML oficial, longitude lunar e identificação conservadora."""
from io import BytesIO
from zipfile import ZipFile

import pytest

from lunar_names import (
    GazetteerUnavailable,
    find_named_features,
    lunar_distance_km,
    parse_usgs_kml,
    parse_usgs_kmz,
    wrap_east_longitude,
)


def _valid_kml():
    points = []
    for i in range(110):
        name = f"Feição Oficial {i}"
        lon = 348.78 if i == 0 else (i * 3.0) % 360
        lat = -43.30 if i == 0 else -35.0
        diameter = "85.29" if i == 0 else "2"
        points.append(
            f"<Placemark><name>{name}</name>"
            f"<ExtendedData><Data name='diameter'><value>{diameter}</value>"
            f"</Data></ExtendedData>"
            f"<Point><coordinates>{lon},{lat},0</coordinates></Point>"
            f"</Placemark>"
        )
    return ("<kml xmlns='http://www.opengis.net/kml/2.2'><Document>"
            + "".join(points) + "</Document></kml>").encode("utf-8")


def test_usgs_kml_reads_lon_0_360_and_diameter():
    names = parse_usgs_kml(_valid_kml())
    assert len(names) == 110
    assert names[0]["name"] == "Feição Oficial 0"
    assert names[0]["lon"] == pytest.approx(-11.22)
    assert names[0]["diameter_km"] == pytest.approx(85.29)


def test_kmz_archive_is_usable_without_network():
    memory = BytesIO()
    with ZipFile(memory, "w") as z:
        z.writestr("doc.kml", _valid_kml())
    names = parse_usgs_kmz(memory.getvalue())
    assert len(names) == 110


def test_lunar_distance_with_date_line_wrap():
    assert wrap_east_longitude(348.78) == pytest.approx(-11.22)
    assert lunar_distance_km(0, 179.9, 0, -179.9) == pytest.approx(6.065, abs=.03)


def test_a_click_inside_nominal_diameter_is_not_claimed_as_geological_contour():
    features = [{
        "name": "Tycho", "lat": -43.3, "lon": -11.22,
        "diameter_km": 85.29,
        "source": "https://planetarynames.wr.usgs.gov/Feature/6163",
        "catalogue": "USGS/IAU",
    }]
    match = find_named_features(-43.35, -11.27, features)
    assert match[0]["name"] == "Tycho"
    assert match[0]["relation"] == "na área nominal"


def test_near_without_diameter_and_no_match_far_away():
    features = [{"name": "N", "lat": 0, "lon": 0, "diameter_km": None}]
    near = find_named_features(0.01, 0.02, features)
    assert near[0]["relation"] == "próximo do centro"
    assert find_named_features(30, 30, features) == []


def test_garbage_xml_is_not_silently_accepted():
    with pytest.raises(GazetteerUnavailable):
        parse_usgs_kml(b"not xml")
