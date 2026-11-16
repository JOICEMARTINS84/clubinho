"""Testes sem rede do explorador lunar baseado apenas em coordenadas."""
import pytest

from lunar_explorer import NASA_WAC_TILES, valid_coords, _map


def test_uses_lunar_not_terrestrial_tiles():
    assert "/Moon/EQ/LRO_WAC_Mosaic_Global_303ppd_v02/" in NASA_WAC_TILES
    assert all(token in NASA_WAC_TILES for token in ("{z}", "{x}", "{y}"))


def test_coordinates_valid_without_a_place_name():
    assert valid_coords(-43.30, -11.22) == (-43.30, -11.22)
    assert valid_coords(0, 0) == (0, 0)


def test_coordinates_out_of_range():
    with pytest.raises(ValueError):
        valid_coords(-91, 0)
    with pytest.raises(ValueError):
        valid_coords(0, 190)


def test_map_marker_has_no_named_geological_feature():
    content = _map(-43.3, -11.22).get_root().render()
    assert "Coordenadas selecionadas" in content
    assert "Tycho" not in content
    assert "Copernicus" not in content


def test_measurement_map_shows_two_manual_edges_without_toponyms():
    rendered = _map(
        -43.30, -11.22, mode="Medir cratera",
        rim_points=[(-43.32, -11.26), (-43.28, -11.18)],
    ).get_root().render()
    assert "Borda A" in rendered
    assert "Borda B" in rendered
    assert "Diâmetro aproximado" in rendered
    assert "Tycho" not in rendered
    assert "Copernicus" not in rendered


def test_single_edge_does_not_yet_render_a_diameter():
    rendered = _map(
        0, 0, mode="Medir cratera", rim_points=[(0, 0.1)]
    ).get_root().render()
    assert "Borda A" in rendered
    assert "Borda B" not in rendered
    assert "Diâmetro aproximado" not in rendered
