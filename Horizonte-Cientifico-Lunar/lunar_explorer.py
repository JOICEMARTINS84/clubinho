"""Explorador geográfico da Lua com mosaico NASA Moon Trek e coleta JPL.

Proveniência:
- imagens de base: NASA/JPL Moon Trek, LRO WAC Mosaic v2 (WMTS)
- crateras nomeadas: catálogo USGS/IAU ou tabela do LPI explicitamente citada
- posições Sol/Terra: NASA/JPL Horizons (consulta específica para o sítio)
- energia e atraso da luz: cálculos em Python, não medições locais
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import folium
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

from horizons import HorizonsError, get_ephemerides
from physics import add_solar_power

NASA_WAC_TILES = (
    "https://trek.nasa.gov/tiles/Moon/EQ/"
    "LRO_WAC_Mosaic_Global_303ppd_v02/1.0.0/default/default028mm/{z}/{y}/{x}.jpg"
)
SOURCE_USGS = "https://planetarynames.wr.usgs.gov/Feature/6163"
SOURCE_LPI = "https://www.lpi.usra.edu/publications/books/planetary_science/appendices.pdf"
MOON_TREK = "https://trek.nasa.gov/moon/"

# Centro (latitude norte+, longitude leste+) e diâmetro nominal (km).
# USGS (Tycho) e tabela Appendix III, LPI (demais crateras).
CRATERS = {
    "Tycho": {"lat": -43.30, "lon": -11.22, "diameter_km": 85.29,
              "source": SOURCE_USGS, "ref": "USGS/IAU · Gazetteer"},
    "Copernicus": {"lat": 9.7, "lon": -20.0, "diameter_km": 93.0,
                    "source": SOURCE_LPI, "ref": "LPI · Apêndice III"},
    "Clavius": {"lat": -58.4, "lon": -14.4, "diameter_km": 225.0,
                "source": SOURCE_LPI, "ref": "LPI · Apêndice III"},
    "Aristarchus": {"lat": 23.7, "lon": -47.4, "diameter_km": 40.0,
                    "source": SOURCE_LPI, "ref": "LPI · Apêndice III"},
    "Archimedes": {"lat": 29.7, "lon": -4.0, "diameter_km": 83.0,
                   "source": SOURCE_LPI, "ref": "LPI · Apêndice III"},
    "Eratosthenes": {"lat": 14.5, "lon": -11.3, "diameter_km": 58.0,
                     "source": SOURCE_LPI, "ref": "LPI · Apêndice III"},
}

LANDING_SITES = {
    "Apollo 11 · Mare Tranquillitatis": {"lat": 0.67416, "lon": 23.47314},
    "Apollo 15 · Hadley Rille": {"lat": 26.13239, "lon": 3.63330},
    "Apollo 17 · Taurus–Littrow": {"lat": 20.19110, "lon": 30.77230},
}

NOMINATED = ["Ponto livre (clique no mapa ou digite coordenadas)"] + [
    f"Cratera · {name}" for name in CRATERS
] + list(LANDING_SITES)


def site_record(name: str):
    if name.startswith("Cratera · "):
        return CRATERS.get(name.replace("Cratera · ", "", 1))
    return LANDING_SITES.get(name)


def valid_coords(lat: float, lon: float) -> tuple[float, float]:
    lat, lon = float(lat), float(lon)
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValueError("As coordenadas lunares devem estar entre ±90° de latitude e ±180° de longitude.")
    return lat, lon


def _init_state() -> None:
    if "lunar_site_lat" not in st.session_state:
        st.session_state.lunar_site_lat = -43.30
        st.session_state.lunar_site_lon = -11.22
        st.session_state.lunar_site_name = "Cratera · Tycho"
        st.session_state.lunar_site_previous_name = "Cratera · Tycho"


def _map(current_lat: float, current_lon: float):
    m = folium.Map(
        location=[current_lat, current_lon],
        zoom_start=4,
        min_zoom=1,
        max_zoom=8,
        tiles=None,
        crs="EPSG4326",  # Equiretangular; Moon Trek usa tile 2x1 em zoom 0
        zoom_control=True,
        prefer_canvas=True,
    )
    folium.TileLayer(
        tiles=NASA_WAC_TILES,
        name="Fotografia global LRO/WAC · NASA Moon Trek",
        attr="NASA/JPL Moon Trek · NASA/GSFC/ASU LRO WAC Mosaic v2",
        min_zoom=0,
        max_zoom=8,
        overlay=False,
        control=False,
        tms=False,
        no_wrap=True,
    ).add_to(m)
    folium.CircleMarker(
        location=[current_lat, current_lon], radius=6,
        color="#f13b2d", fill=True, fill_color="#f13b2d",
        fill_opacity=0.85, weight=2,
        tooltip="Ponto selecionado",
    ).add_to(m)
    return m


@st.cache_data(ttl=3600, show_spinner=False)
def _query_site(lat, lon, start, stop, step):
    return get_ephemerides(lat, lon, start, stop, step)


def _selection_callback() -> None:
    """Lê o clique antes dos widgets renderizarem na execução seguinte."""
    output = st.session_state.get("moon_wac_map") or {}
    click = output.get("last_clicked") if isinstance(output, dict) else None
    if not isinstance(click, dict):
        return
    try:
        la, lo = valid_coords(click["lat"], click["lng"])
    except (KeyError, ValueError, TypeError):
        return
    st.session_state.lunar_site_lat = round(la, 5)
    st.session_state.lunar_site_lon = round(lo, 5)
    st.session_state.lunar_site_name = NOMINATED[0]
    st.session_state.lunar_site_previous_name = NOMINATED[0]
    st.session_state["lunar_place_choice"] = NOMINATED[0]
    st.session_state.pop("lunar_site_results", None)
    st.session_state.pop("lunar_site_query_key", None)


def _apply_manual_coordinates() -> None:
    try:
        la, lo = valid_coords(st.session_state["lunar_manual_lat"],
                              st.session_state["lunar_manual_lon"])
    except (ValueError, KeyError, TypeError):
        return
    st.session_state.lunar_site_lat = round(la, 5)
    st.session_state.lunar_site_lon = round(lo, 5)
    st.session_state.lunar_site_name = NOMINATED[0]
    st.session_state.lunar_site_previous_name = NOMINATED[0]
    st.session_state["lunar_place_choice"] = NOMINATED[0]
    st.session_state.pop("lunar_site_results", None)
    st.session_state.pop("lunar_site_query_key", None)


def render_lunar_explorer(start: datetime, stop: datetime, step: int,
                          area: float, efficiency: float, mode: str,
                          tilt: float = 0.0, az_panel: float = 0.0):
    _init_state()
    st.subheader("Escolha um local. Colete as informações.")
    st.caption("Mapa lunar fotográfico da NASA/LRO · Clique no mapa ou selecione uma cratera por nome. "
               "A latitude e a longitude são planetográficas neste visualizador.")

    choice = st.selectbox(
        "Pesquisar um local lunar",
        NOMINATED,
        index=NOMINATED.index(st.session_state.lunar_site_name)
        if st.session_state.lunar_site_name in NOMINATED else 0,
        key="lunar_place_choice",
        help="Nomes de crateras vêm de catálogos científicos, não de reconhecimento por IA.",
    )
    if choice != st.session_state.lunar_site_previous_name:
        record = site_record(choice)
        if record:
            st.session_state.lunar_site_lat = record["lat"]
            st.session_state.lunar_site_lon = record["lon"]
        st.session_state.lunar_site_name = choice
        st.session_state.lunar_site_previous_name = choice
        st.session_state.pop("lunar_site_results", None)
        st.session_state.pop("lunar_site_query_key", None)

    lat = float(st.session_state.lunar_site_lat)
    lon = float(st.session_state.lunar_site_lon)
    current = site_record(st.session_state.lunar_site_name)

    left, right = st.columns([1.7, 1.0], gap="large")
    with left:
        st.markdown("**01 — Selecione no mapa lunar**")
        st.caption("Roda do mouse aproxima. Clique em qualquer ponto da superfície para marcar as coordenadas.")
        st_folium(
            _map(lat, lon),
            key="moon_wac_map",
            use_container_width=True,
            height=455,
            returned_objects=["last_clicked"],
            on_change=_selection_callback,
        )
        st.caption("Mosaico global NASA Moon Trek, missão LRO/WAC. Coordenadas de mapa e fotos "
                   "não equivalem a medição altimétrica.")
    with right:
        st.markdown("**02 — Coordenadas selecionadas**")
        st.metric("Latitude lunar", f"{lat:+.5f}°")
        st.metric("Longitude leste", f"{lon:+.5f}°")
        if current and "diameter_km" in current:
            st.metric("Diâmetro de catálogo", f"{current['diameter_km']:.2f} km")
            st.caption(f"{current['ref']}. Tamanho nominal da cratera, não medido nesta foto.")
            st.markdown(f"[Consultar fonte do catálogo]({current['source']})")
        elif current:
            st.caption("Local histórico aproximado. Não é cratera; sem diâmetro catalogado.")
        else:
            st.caption("Ponto livre: sem cratera identificada automaticamente. "
                       "As coordenadas serão usadas para a consulta astronômica.")
        with st.expander("Digitar coordenadas exatas"):
            with st.form("manual_lunar_coords"):
                st.number_input("Latitude norte (+) / sul (−)", -90.0, 90.0, lat,
                                step=0.01, format="%.5f", key="lunar_manual_lat")
                st.number_input("Longitude leste (+) / oeste (−)", -180.0, 180.0, lon,
                                step=0.01, format="%.5f", key="lunar_manual_lon")
                st.form_submit_button("Aplicar coordenadas", use_container_width=True,
                                      on_click=_apply_manual_coordinates)
        st.markdown("[Abrir mapas de altitude e buscar imagens NAC na NASA Moon Trek]"
                    f"({MOON_TREK})")

    st.markdown("**03 — Coleta de dados para o ponto selecionado**")
    st.caption("Os valores do catálogo e a fotografia já podem ser consultados. "
               "O botão busca efemérides Sol/Terra especificamente para as coordenadas acima.")
    collect_key = (round(lat,5), round(lon,5), start.isoformat(), stop.isoformat(), int(step))
    collected = st.button(
        "Coletar efemérides NASA/JPL deste local", type="primary", use_container_width=True,
        key="collect_lunar_site",
    )
    if collected:
        try:
            with st.spinner("Consultando Sol e Terra no JPL Horizons para o local selecionado..."):
                result = _query_site(lat, lon, start, stop, step)
            st.session_state.lunar_site_results = result
            st.session_state.lunar_site_query_key = collect_key
            st.session_state.pop("lunar_site_error", None)
        except (HorizonsError, ValueError, KeyError) as exc:
            st.session_state.lunar_site_error = str(exc)
            st.session_state.pop("lunar_site_results", None)
            st.session_state.pop("lunar_site_query_key", None)
    if st.session_state.get("lunar_site_error"):
        st.error("A consulta ao JPL não foi concluída: " + st.session_state.lunar_site_error)
        st.caption("O mapa e o catálogo continuam disponíveis, mas nenhuma efeméride fictícia foi gerada.")

    meta = {
        "instrumento_cartografico": "LRO Wide Angle Camera (WAC); NASA Moon Trek",
        "mapa_wmts": NASA_WAC_TILES,
        "fonte_nomenclatura": (current or {}).get("source"),
        "local": st.session_state.lunar_site_name,
        "lat_graus": lat,
        "lon_leste_graus": lon,
        "diametro_catalogo_km": (current or {}).get("diameter_km"),
        "periodo_inicio_utc": start.isoformat(),
        "periodo_fim_utc": stop.isoformat(),
        "passo_horas": int(step),
        "fonte_efemerides": "NASA/JPL Horizons",
        "estado_efemerides": "não consultado",
        "nota_cientifica": "Imagens LRO não são DEM; nenhum valor de altitude/profundidade foi inventado.",
        "gerado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    data = st.session_state.get("lunar_site_results")
    if data is not None and st.session_state.get("lunar_site_query_key") == collect_key:
        try:
            computed = add_solar_power(data, area, efficiency, mode, tilt, az_panel)
            meta["estado_efemerides"] = "obtido da API JPL Horizons"
            meta["amostras"] = len(computed)
            st.success(f"Consulta concluída: {len(computed)} amostras astronômicas.")
            sample = computed.iloc[0]
            a,b,c,d = st.columns(4)
            a.metric("Sol · elevação", f"{sample['sun_elev']:.2f}°")
            b.metric("Terra · elevação", f"{sample['earth_elev']:.2f}°")
            c.metric("Distância à Terra", f"{sample['earth_dist_km']:,.0f} km")
            d.metric("Luz até a Terra", f"{sample['retardo_terra_s']:.2f} s")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=computed["instante_utc"],y=computed["sun_elev"],
                                     name="Sol",line=dict(color="#f1d7a8", width=2.5)))
            fig.add_trace(go.Scatter(x=computed["instante_utc"],y=computed["earth_elev"],
                                     name="Terra",line=dict(color="#75b6ed",width=2.5)))
            fig.add_hline(y=0,line_color="#9aaabe",line_dash="dot")
            fig.update_layout(template="plotly_dark",height=360,
                              paper_bgcolor="#05080e",plot_bgcolor="#05080e",
                              xaxis_title="Data e hora (UTC)",yaxis_title="Elevação (°)",
                              margin=dict(l=10,r=10,t=10,b=30),legend=dict(orientation="h"))
            st.plotly_chart(fig,use_container_width=True)
            st.dataframe(computed,hide_index=True,use_container_width=True)
            st.download_button("Baixar séries astronômicas e cálculos (CSV)",
                               data=computed.to_csv(index=False).encode("utf-8-sig"),
                               file_name="local_lunar_efemerides.csv",mime="text/csv",
                               key="lunar_site_csv")
            st.caption("Efemérides e distâncias: JPL Horizons; atraso da luz e energia solar: "
                       "modelos matemáticos. A elevação dos astros não incorpora sombras do terreno.")
        except (ValueError, KeyError, TypeError) as exc:
            st.error(f"Não foi possível interpretar os dados obtidos: {str(exc)[:220]}.")
            meta["estado_efemerides"] = "falha de interpretação"

    st.download_button("Baixar ficha do local e proveniência (JSON)",
                       data=json.dumps(meta,ensure_ascii=False,indent=2).encode("utf-8"),
                       file_name="ficha_local_lunar.json",
                       mime="application/json",key="lunar_site_json")
    st.caption("O Moon Trek possui perfis de altitude e busca de imagens NAC, mas esses dados "
               "ainda não são importados automaticamente para esta ficha. "
               "Só apresentaremos profundidade ou altitude quando associadas a um DEM verificado.")
