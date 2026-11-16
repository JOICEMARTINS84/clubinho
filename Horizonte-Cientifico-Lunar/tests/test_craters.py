"""Testes sem rede para análise de brilho de uma imagem sintética."""
import numpy as np
import pytest
from PIL import Image

from craters import _decode_image, sample_brightness_line, PHOTO_SOURCES


def test_brightness_profile_uses_real_pixel_values():
    arr = np.full((11, 13, 3), 10, dtype=np.uint8)
    arr[:, 6:, :] = 210
    im = Image.fromarray(arr)
    profile = sample_brightness_line(im, 6, 5, 4)
    assert profile.shape[0] == 9
    assert profile["deslocamento_px"].tolist() == list(range(-4, 5))
    assert profile["brilho_0_255"].iloc[0] == pytest.approx(10)
    assert profile["brilho_0_255"].iloc[-1] == pytest.approx(210)


def test_reject_invalid_image_bytes():
    with pytest.raises(ValueError):
        _decode_image(b"not a photograph")


def test_nasa_sources_have_credits_and_documented_pages():
    for metadata in PHOTO_SOURCES.values():
        assert metadata["url"].startswith("https://")
        assert metadata["page"].startswith("https://")
        assert "NASA" in metadata["credit"]
