"""Consulta efemérides topocêntricas do JPL Horizons para locais na Lua.

Fonte: https://ssd.jpl.nasa.gov/api/horizons.api
A saída é observacional, sem um modelo de obstrução por relevo.
"""
from __future__ import annotations

import csv
import re
from datetime import datetime, timezone

import pandas as pd
import requests

API_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"
TARGETS = {"sun": "10", "earth": "399"}
NUMBER = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?")
DATE = re.compile(r"^\s*(?:A\.D\.\s*)?(\d{4}-[A-Za-z]{3}-\d{2}\s+\d{2}:\d{2})")


class HorizonsError(RuntimeError):
    """Erro de consulta ou formato inesperado do Horizons."""


def parse_horizons_csv(text: str, target: str) -> pd.DataFrame:
    """Extrai azimute e elevação de QUANTITIES=4 e CSV_FORMAT=YES.

    Os campos finais numéricos são azimute e elevação; colunas de visibilidade
    e marcadores do observador podem antecedê-los. Não inventa dados faltantes.
    """
    if "$$SOE" not in text or "$$EOE" not in text:
        details = text[:450].strip().replace("\n", " ")
        raise HorizonsError(f"A resposta do Horizons não contém uma tabela válida: {details}")
    rows = []
    section = text.split("$$SOE", 1)[1].split("$$EOE", 1)[0]
    for line in section.splitlines():
        if not line.strip():
            continue
        cells = next(csv.reader([line], skipinitialspace=True))
        if not cells:
            continue
        match = DATE.match(cells[0])
        if not match:
            continue
        try:
            timestamp = datetime.strptime(match.group(1), "%Y-%b-%d %H:%M").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        numbers = [float(c.strip()) for c in cells[1:] if NUMBER.fullmatch(c.strip())]
        if len(numbers) < 2:
            continue
        azimuth, altitude = numbers[-2], numbers[-1]
        if not 0.0 <= azimuth <= 360.0 or not -90.0 <= altitude <= 90.0:
            continue
        rows.append((timestamp, azimuth, altitude))
    if not rows:
        raise HorizonsError("A API respondeu, mas não encontramos azimute/elevação legíveis.")
    return pd.DataFrame(rows, columns=["instante_utc", f"{target}_az", f"{target}_elev"])


def request_body(
    target: str,
    latitude: float,
    longitude: float,
    start: datetime,
    stop: datetime,
    step_hours: int,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    if target not in TARGETS:
        raise ValueError(f"Alvo desconhecido: {target}")
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("Latitude/longitude fora da faixa permitida.")
    if step_hours not in (3, 6, 12):
        raise ValueError("O intervalo deve ser 3, 6 ou 12 horas.")
    # Longitudes de -180° a 180° são equivalentes a 0° a 360° leste.
    east_lon = longitude % 360.0
    params = {
        "format": "json",
        "COMMAND": f"'{TARGETS[target]}'",
        "OBJ_DATA": "'NO'",
        "MAKE_EPHEM": "'YES'",
        "EPHEM_TYPE": "'OBSERVER'",
        "CENTER": "'coord@301'",  # corpo 301 = Lua
        "COORD_TYPE": "'GEODETIC'",
        "SITE_COORD": f"'{east_lon:.6f},{latitude:.6f},0'",  # km acima elipsoide
        "START_TIME": f"'{start:%Y-%m-%d %H:%M}'",
        "STOP_TIME": f"'{stop:%Y-%m-%d %H:%M}'",
        "STEP_SIZE": f"'{step_hours}h'",
        "QUANTITIES": "'4'",  # azimute e elevação aparentes
        "CSV_FORMAT": "'YES'",
        "ANG_FORMAT": "'DEG'",
        "TIME_TYPE": "'UT'",
        "TIME_DIGITS": "'MINUTES'",
        "APPARENT": "'AIRLESS'",  # geometria sem correção atmosférica
    }
    client = session if session is not None else requests
    try:
        response = client.get(API_URL, params=params, timeout=55)
        if response.status_code >= 400:
            try:
                response_error = response.json()
                details = response_error.get("message") or response_error.get("error") or response.text
            except ValueError:
                details = response.text
            details = " ".join(str(details).split())[:600]
            raise HorizonsError(
                f"JPL Horizons rejeitou a consulta (HTTP {response.status_code}). "
                f"Detalhe da NASA: {details or 'sem detalhes adicionais'}"
            )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise HorizonsError(f"Não foi possível consultar o JPL Horizons: {exc}") from exc
    if payload.get("error"):
        raise HorizonsError(f"O Horizons informou um erro: {payload['error']}")
    if not isinstance(payload.get("result"), str):
        raise HorizonsError("Resposta inválida: resultado textual ausente.")
    return parse_horizons_csv(payload["result"], target)


def get_ephemerides(latitude: float, longitude: float, start: datetime, stop: datetime, step_hours: int) -> pd.DataFrame:
    with requests.Session() as session:
        sun = request_body("sun", latitude, longitude, start, stop, step_hours, session)
        earth = request_body("earth", latitude, longitude, start, stop, step_hours, session)
    df = sun.merge(earth, on="instante_utc", how="inner", validate="one_to_one")
    if df.empty:
        raise HorizonsError("Sol e Terra não apresentaram instantes UTC coincidentes.")
    return df.sort_values("instante_utc").reset_index(drop=True)
