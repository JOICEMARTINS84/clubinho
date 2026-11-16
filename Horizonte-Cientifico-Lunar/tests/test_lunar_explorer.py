"""Testes da seleção cartográfica lunar sem fazer consultas externas."""
import pytest
from lunar_explorer import CRATERS, NOMINATED, NASA_WAC_TILES, valid_coords, site_record

def test_wmts_uses_moon_not_earth():
    assert "/Moon/EQ/LRO_WAC_Mosaic_Global_303ppd_v02/" in NASA_WAC_TILES
    assert all(part in NASA_WAC_TILES for part in ("{z}", "{x}", "{y}"))

def test_catalogued_tycho_has_traceable_source():
    tycho = site_record("Cratera · Tycho")
    assert tycho["diameter_km"] == pytest.approx(85.29)
    assert tycho["lat"] == pytest.approx(-43.30)
    assert "usgs.gov" in tycho["source"]
    assert len(CRATERS) >= 5

def test_free_location_does_not_invent_a_crater():
    assert site_record(NOMINATED[0]) is None

def test_coords_and_limits():
    assert valid_coords(-45.5, 130.2) == (-45.5, 130.2)
    with pytest.raises(ValueError):
        valid_coords(-91.0, 0)
    with pytest.raises(ValueError):
        valid_coords(0, 190)
