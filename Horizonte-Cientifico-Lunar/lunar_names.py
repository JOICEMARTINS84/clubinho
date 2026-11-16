"""Identificação conservadora de topônimos lunares IAU/USGS por coordenadas.

A fonte oficial é o KML de centros de feições do Gazetteer, que a USGS
regenera diariamente. Centro e diâmetro são atributos nominais, não
geometrias de contorno geológico. Distâncias são esféricas aproximadas.
"""
from __future__ import annotations

from io import BytesIO
import math
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile, BadZipFile

import requests
import streamlit as st

KMZ_URL = (
    "https://asc-planetarynames-data.s3.us-west-2.amazonaws.com/"
    "MOON_nomenclature_center_pts.kmz"
)
GAZETTEER_URL = "https://planetarynames.wr.usgs.gov/GIS_Downloads"
FEATURE_URL_ROOT = "https://planetarynames.wr.usgs.gov/Feature/"
MOON_RADIUS_KM = 1737.4
MAX_DOWNLOAD_BYTES = 24_000_000
MAX_KML_UNCOMPRESSED = 52_000_000
MAX_NEARBY_KM = 8.0


class GazetteerUnavailable(RuntimeError):
    """Não foi possível abrir um catálogo oficial identificável."""


def wrap_east_longitude(value: float) -> float:
    """Converte 0..360 E e -180..180 E para a representação -180..180."""
    return (float(value) + 180.0) % 360.0 - 180.0


def lunar_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distância de grande círculo na Lua, raio médio adotado de 1737,4 km."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(wrap_east_longitude(lon2 - lon1))
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * MOON_RADIUS_KM * math.asin(min(1.0, math.sqrt(max(0.0, a))))


def _local_tag(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child_text(placemark: ET.Element, tagname: str) -> str | None:
    for element in placemark.iter():
        if _local_tag(element.tag) == tagname:
            value = (element.text or "").strip()
            if value:
                return value
    return None


def parse_usgs_kml(kml: bytes) -> list[dict]:
    """Lê PlaceMarks com Point; ignora Polygons/LineStrings sem ponto."""
    if len(kml) > MAX_KML_UNCOMPRESSED:
        raise GazetteerUnavailable("O arquivo KML excedeu o limite de segurança.")
    try:
        root = ET.fromstring(kml)
    except ET.ParseError as exc:
        raise GazetteerUnavailable("O catálogo KML da USGS não é legível.") from exc

    features: list[dict] = []
    for elem in root.iter():
        if _local_tag(elem.tag) != "Placemark":
            continue
        name = _child_text(elem, "name")
        coords_text = None
        for point in elem.iter():
            if _local_tag(point.tag) == "Point":
                coords_text = _child_text(point, "coordinates")
                break
        if not name or not coords_text:
            continue
        try:
            tokens = coords_text.split()[0].split(",")
            lon, lat = float(tokens[0]), float(tokens[1])
            if not (math.isfinite(lon) and math.isfinite(lat) and -90 <= lat <= 90):
                continue
        except (ValueError, IndexError):
            continue

        # Optional: KML producers may put diameter in ExtendedData or in HTML description.
        diam = None
        for element in elem.iter():
            if _local_tag(element.tag) in ("SimpleData", "Data"):
                name_attr = (element.attrib.get("name") or "").lower()
                if "diameter" not in name_attr and name_attr not in ("diam", "diam_km"):
                    continue
                val = _child_text(element, "value") if _local_tag(element.tag) == "Data" else element.text
                try:
                    number = float((val or "").strip().replace(",", "."))
                    if 0.0 < number < 5000:
                        diam = number
                        break
                except ValueError:
                    pass

        desc = _child_text(elem, "description") or ""
        feature_id = re.search(
            r"(?:planetarynames\.wr\.usgs\.gov|planetarynames\.usgs\.gov)/(?:Feature|feature)/(\d+)",
            desc,
        )
        features.append({
            "name": name,
            "lat": lat,
            "lon": wrap_east_longitude(lon),
            "diameter_km": diam,
            "source": FEATURE_URL_ROOT + feature_id.group(1) if feature_id else GAZETTEER_URL,
            "catalogue": "Gazetteer USGS/IAU",
        })
    if len(features) < 100:
        raise GazetteerUnavailable(
            "O arquivo recebido não contém uma lista completa de topônimos lunares."
        )
    return features


def parse_usgs_kmz(data: bytes) -> list[dict]:
    if len(data) > MAX_DOWNLOAD_BYTES:
        raise GazetteerUnavailable("O arquivo comprimido é maior que o limite de segurança.")
    try:
        with ZipFile(BytesIO(data)) as archive:
            members = [info for info in archive.infolist()
                       if info.filename.lower().endswith(".kml")
                       and info.file_size < MAX_KML_UNCOMPRESSED]
            if not members:
                raise GazetteerUnavailable("O pacote USGS não contém um KML compatível.")
            members.sort(key=lambda entry: entry.file_size, reverse=True)
            return parse_usgs_kml(archive.read(members[0]))
    except (BadZipFile, OSError, RuntimeError) as exc:
        raise GazetteerUnavailable("Não foi possível ler o pacote geográfico oficial.") from exc


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_usgs_names() -> list[dict]:
    """Busca apenas arquivo fixo oficial, por HTTPS, e guarda em cache por 24 h."""
    try:
        with requests.get(KMZ_URL, timeout=35, stream=True) as response:
            response.raise_for_status()
            payload = bytearray()
            for chunk in response.iter_content(chunk_size=64 * 1024):
                payload.extend(chunk)
                if len(payload) > MAX_DOWNLOAD_BYTES:
                    raise GazetteerUnavailable("O catálogo USGS excedeu o limite de download.")
        return parse_usgs_kmz(bytes(payload))
    except requests.RequestException as exc:
        raise GazetteerUnavailable(
            "O catálogo de nomes USGS/IAU está temporariamente inacessível."
        ) from exc


def find_named_features(
    lat: float, lon: float, features: list[dict], max_nearby_km: float = MAX_NEARBY_KM
) -> list[dict]:
    """Estima correspondência com limites nominais de diâmetro; sem inventar contornos.

    In-area: centro a <= diâmetro/2, somente se diâmetro foi fornecido.
    Near: centro a <= max_nearby_km, caso não esteja dentro de um diâmetro
    cadastrado. Nunca transforma uma associação de proximidade em contenção.
    """
    candidates = []
    for feat in features:
        try:
            dist = lunar_distance_km(lat, lon, feat["lat"], feat["lon"])
            nominal_diameter = feat.get("diameter_km")
            inside = (
                nominal_diameter is not None
                and nominal_diameter > 0
                and dist <= nominal_diameter / 2
            )
            if inside or dist <= max_nearby_km:
                candidates.append({
                    **feat,
                    "distance_km": round(dist, 2),
                    "relation": "na área nominal" if inside else "próximo do centro",
                })
        except (KeyError, TypeError, ValueError):
            continue

    # Para feições contidas, prioriza centro relativo ao tamanho nominal.
    # Onde não temos diâmetro, só declaramos proximidade.
    candidates.sort(key=lambda f: (
        0 if f["relation"] == "na área nominal" else 1,
        f["distance_km"] / (max(0.01, f.get("diameter_km") or 0.02)) if
        f["relation"] == "na área nominal" else f["distance_km"]
    ))
    return candidates[:4]
