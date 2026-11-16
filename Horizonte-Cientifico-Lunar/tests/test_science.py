from datetime import datetime, timezone

import pandas as pd
import pytest

from horizons import HorizonsError, parse_horizons_csv, request_body
from physics import add_solar_power, fator_incidencia

EXAMPLE = """Target body name: Sun (10)
$$SOE
 2026-Nov-16 00:00,*, ,  180.000,   10.000,
 2026-Nov-16 06:00, , ,  190.000,   -5.000,
 2026-Nov-16 12:00,*, ,  200.000,    5.000,
$$EOE
"""


def test_parse_two_angles_and_utc():
    df = parse_horizons_csv(EXAMPLE, "sun")
    assert len(df) == 3
    assert df.iloc[0]["sun_az"] == 180.0
    assert df.iloc[1]["sun_elev"] == -5.0
    assert df.iloc[0]["instante_utc"].tzinfo == timezone.utc


def test_no_fake_results_on_api_error():
    with pytest.raises(HorizonsError):
        parse_horizons_csv("no data", "sun")


def test_orientation_and_darkness():
    assert fator_incidencia(-1, 0, "Rastreamento ideal") == 0
    assert fator_incidencia(20, 20, "Rastreamento ideal") == 1
    assert fator_incidencia(90, 0, "Horizontal") == pytest.approx(1)
    assert fator_incidencia(10, 90, "Inclinado fixo", 80, 90) == pytest.approx(1)
    assert fator_incidencia(10, 270, "Inclinado fixo", 80, 90) == 0


def test_energy_constant_power_and_integration():
    times = pd.date_range("2026-11-16", periods=3, freq="6h", tz="UTC")
    df = pd.DataFrame({"instante_utc": times, "sun_elev": [20., 20., 20.],
                       "sun_az": [0., 0., 0.]})
    result = add_solar_power(df, area_m2=2, efficiency_pct=25, mode="Rastreamento ideal")
    assert result["potencia_w"].iloc[0] == pytest.approx(680.5)
    assert result["energia_acumulada_kwh"].iloc[-1] == pytest.approx(8.166)


def test_reject_invalid_site():
    with pytest.raises(ValueError):
        request_body("sun", -92, 0, datetime.now(timezone.utc), datetime.now(timezone.utc), 6)


def test_horizons_request_uses_supported_parameters():
    class StubResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"result": EXAMPLE}

    class StubSession:
        params = None

        def get(self, _url, params, timeout):
            self.params = params
            return StubResponse()

    session = StubSession()
    result = request_body(
        "sun", -89.5, 0.0,
        datetime(2026, 11, 16, tzinfo=timezone.utc),
        datetime(2026, 11, 17, tzinfo=timezone.utc),
        6, session,
    )
    assert len(result) == 3
    assert session.params["APPARENT"] == "'AIRLESS'"
    assert "REFRACT" not in session.params


def test_horizons_http_error_shows_nasa_message():
    class StubResponse:
        status_code = 400
        text = '{"message": "Invalid input keyword"}'

        def json(self):
            return {"message": "Invalid input keyword"}

    class StubSession:
        def get(self, _url, params, timeout):
            return StubResponse()

    with pytest.raises(HorizonsError, match="Invalid input keyword"):
        request_body(
            "sun", -89.5, 0,
            datetime(2026, 11, 16, tzinfo=timezone.utc),
            datetime(2026, 11, 17, tzinfo=timezone.utc),
            6, StubSession(),
        )
