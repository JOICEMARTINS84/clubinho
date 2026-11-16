"""Explorador lunar por coordenadas, usando mapa NASA Moon Trek e NASA/JPL Horizons.

Este módulo não identifica nem atribui nomes a formações geológicas.
Um clique seleciona somente latitude e longitude; nomes podem ser
consultados externamente em fontes oficiais, sem correspondência automática.
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
from crater_measure import MOON_RADIUS_KM, estimate_crater, spherical_midpoint

NASA_WAC_TILES = (
    "https://trek.nasa.gov/tiles/Moon/EQ/"
    "LRO_WAC_Mosaic_Global_303ppd_v02/1.0.0/default/default028mm/{z}/{y}/{x}.jpg"
)
MOON_TREK = "https://trek.nasa.gov/moon/"


def valid_coords(lat: float, lon: float) -> tuple[float, float]:
    lat, lon = float(lat), float(lon)
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValueError("Latitude deve estar entre -90° e 90°; longitude entre -180° e 180°.")
    return lat, lon


def _init_state() -> None:
    if "lunar_site_lat" not in st.session_state:
        # Ponto de estudo neutro: não atribuímos nome a nenhuma formação.
        st.session_state.lunar_site_lat = 0.0
        st.session_state.lunar_site_lon = 0.0
    if "lunar_rim_points" not in st.session_state:
        st.session_state.lunar_rim_points = []
    # Limpa estados de versões antigas que faziam identificação automática.
    for key in (
        "lunar_identify_active", "lunar_site_name", "lunar_site_previous_name",
        "lunar_place_choice",
    ):
        st.session_state.pop(key, None)


def _map(
    current_lat: float, current_lon: float,
    mode: str = "Selecionar ponto",
    rim_points: list[tuple[float, float]] | None = None,
) -> folium.Map:
    """Renderiza foto LRO, marcador de posição OU duas bordas escolhidas."""
    m = folium.Map(
        location=[current_lat, current_lon], zoom_start=4,
        min_zoom=1, max_zoom=8, tiles=None, crs="EPSG4326",
        zoom_control=True, prefer_canvas=True,
    )
    folium.TileLayer(
        tiles=NASA_WAC_TILES,
        name="Mosaico fotográfico lunar LRO/WAC · NASA Moon Trek",
        attr="NASA/JPL Moon Trek · NASA/GSFC/ASU LRO WAC Mosaic v2",
        min_zoom=0, max_zoom=8, overlay=False, control=False,
        tms=False, no_wrap=True,
    ).add_to(m)

    points = rim_points or []
    if mode == "Medir cratera":
        for index, (latitude, longitude) in enumerate(points[:2]):
            label = "A" if index == 0 else "B"
            color = "#f7d08c" if index == 0 else "#65bcf5"
            folium.CircleMarker(
                location=[latitude, longitude], radius=8,
                color=color, fill=True, fill_color=color,
                fill_opacity=0.95, weight=3,
                tooltip=f"Borda {label} • {latitude:+.5f}°, {longitude:+.5f}°",
            ).add_to(m)
        if len(points) == 2:
            if abs(points[0][1] - points[1][1]) <= 180:
                folium.PolyLine(
                    locations=points, color="#f13b2d", weight=3,
                    opacity=0.9, tooltip="Diâmetro aproximado entre as bordas A e B",
                ).add_to(m)
            folium.CircleMarker(
                location=[current_lat, current_lon], radius=4,
                color="white", fill=True, fill_color="#f13b2d",
                fill_opacity=1.0, weight=2,
                tooltip="Centro geométrico estimado (não centro real medido)",
            ).add_to(m)
    else:
        folium.CircleMarker(
            location=[current_lat, current_lon], radius=6,
            color="#f13b2d", fill=True, fill_color="#f13b2d",
            fill_opacity=0.85, weight=2,
            tooltip="Coordenadas selecionadas — sem identificação de nome",
        ).add_to(m)
    return m


@st.cache_data(ttl=3600, show_spinner=False)
def _query_site(lat, lon, start, stop, step):
    return get_ephemerides(lat, lon, start, stop, step)


def _set_location(lat: float, lon: float) -> None:
    la, lo = valid_coords(lat, lon)
    old_position = (
        st.session_state.get("lunar_site_lat"),
        st.session_state.get("lunar_site_lon"),
    )
    position = (round(la, 5), round(lo, 5))
    if old_position != position:
        st.session_state.lunar_site_lat = position[0]
        st.session_state.lunar_site_lon = position[1]
        st.session_state.pop("lunar_site_results", None)
        st.session_state.pop("lunar_site_query_key", None)
        st.session_state.pop("lunar_site_error", None)


def _selection_callback() -> None:
    """Converte um clique em ponto de pesquisa ou em borda A/B, conforme o modo."""
    result = st.session_state.get("moon_wac_map") or {}
    click = result.get("last_clicked") if isinstance(result, dict) else None
    if not isinstance(click, dict):
        return
    try:
        la, lo = valid_coords(click["lat"], click["lng"])
        position = (round(la, 6), round(lo, 6))
    except (KeyError, ValueError, TypeError):
        return

    # Evita contabilizar novamente o mesmo evento caso o mapa seja redesenhado.
    if st.session_state.get("lunar_last_click") == position:
        return
    st.session_state.lunar_last_click = position

    if st.session_state.get("lunar_action_mode", "Selecionar ponto") != "Medir cratera":
        _set_location(*position)
        return

    points = list(st.session_state.get("lunar_rim_points", []))
    if len(points) >= 2:
        return  # só reiniciar para efetuar nova medida
    if points and points[-1] == position:
        return
    points.append(position)
    st.session_state.lunar_rim_points = points
    if len(points) == 1:
        _set_location(*position)
    else:
        try:
            midpoint = spherical_midpoint(points[0], points[1])
            _set_location(*midpoint)
        except ValueError:
            # Pontos antipodais: geometria sem centro único; explicar na UI.
            pass


def _clear_crater_measurement() -> None:
    """Inicia uma nova medida sem alterar as coordenadas de consulta já escolhidas."""
    st.session_state.lunar_rim_points = []



def _apply_manual_coordinates() -> None:
    try:
        _set_location(
            st.session_state["lunar_manual_lat"],
            st.session_state["lunar_manual_lon"],
        )
    except (KeyError, ValueError, TypeError):
        pass


def render_lunar_explorer(
    start: datetime, stop: datetime, step: int,
    area: float, efficiency: float, mode: str,
    tilt: float = 0.0, az_panel: float = 0.0,
) -> None:
    _init_state()
    st.subheader("Explorador lunar · selecionar e medir")
    st.caption(
        "Mapa fotográfico da NASA/LRO. Os cliques retornam apenas coordenadas, "
        "sem identificação automática de crateras ou outros nomes."
    )
    action = st.radio(
        "O que você deseja fazer?",
        ["Selecionar ponto", "Medir cratera"],
        horizontal=True,
        key="lunar_action_mode",
        help="Selecionar ponto: pesquisar efemérides. Medir cratera: marque duas bordas opostas para calcular um diâmetro aproximado.",
    )
    rim_points = list(st.session_state.get("lunar_rim_points", []))
    if action == "Medir cratera":
        st.info(
            "**Como medir:** aproxime o mapa e clique na borda A da cratera. "
            "Depois clique na borda B, no lado oposto. O programa calcula "
            "a distância entre os pontos usando o raio médio da Lua."
        )
        if rim_points:
            st.button(
                "Recomeçar medição · apagar A e B",
                on_click=_clear_crater_measurement,
                key="crater_clear_points",
            )
            rim_points = list(st.session_state.get("lunar_rim_points", []))

    lat, lon = valid_coords(
        st.session_state.lunar_site_lat,
        st.session_state.lunar_site_lon,
    )

    crater_estimate = None
    if action == "Medir cratera" and len(rim_points) == 2:
        try:
            crater_estimate = estimate_crater(rim_points[0], rim_points[1])
        except ValueError as exc:
            st.warning(f"Não foi possível calcular a medida: {exc}")

    col_map, col_details = st.columns([1.7, 1.0], gap="large")
    with col_map:
        st.markdown("**01 — Marque as bordas no mapa**" if action == "Medir cratera"
                    else "**01 — Selecione um ponto no mapa**")
        if action == "Medir cratera":
            st.caption(
                f"{len(rim_points)}/2 bordas selecionadas · "
                + ("Clique na borda A." if not rim_points
                   else "Clique na borda B (oposta)." if len(rim_points) == 1
                   else "Medição concluída. Reinicie para medir outra região.")
            )
        else:
            st.caption("Use a roda do mouse para aproximar e clique na região que deseja investigar.")

        st_folium(
            _map(lat, lon, mode=action, rim_points=rim_points),
            key="moon_wac_map",
            use_container_width=True,
            height=455,
            returned_objects=["last_clicked"],
            on_change=_selection_callback,
        )
        st.caption(
            "Base cartográfica: mosaico NASA Moon Trek / LRO-WAC. A distância entre "
            "pontos é estimada sobre uma esfera lunar, sem corrigir o relevo."
        )

    with col_details:
        if action == "Medir cratera":
            st.markdown("**02 — Medidas do relevo aparente**")
            if not rim_points:
                st.caption("Nenhuma borda marcada. O primeiro clique definirá a borda A.")
            for index, point in enumerate(rim_points[:2]):
                label = "A" if index == 0 else "B"
                st.caption(
                    f"**Borda {label}:** latitude {point[0]:+.5f}°, "
                    f"longitude {point[1]:+.5f}°"
                )
            if crater_estimate is not None:
                st.metric(
                    "Diâmetro aproximado", f"{crater_estimate.diameter_km:.2f} km",
                    help="Distância superficial pelo arco menor entre os dois pontos clicados.",
                )
                st.metric("Raio estimado", f"{crater_estimate.radius_km:.2f} km")
                st.metric(
                    "Área circular estimada", f"{crater_estimate.area_km2:.2f} km²",
                    help="Área de um círculo plano ideal: π × (diâmetro/2)².",
                )
                st.caption(
                    f"Centro geométrico aproximado: {crater_estimate.midpoint[0]:+.5f}°, "
                    f"{crater_estimate.midpoint[1]:+.5f}°"
                )
                st.success("Distância calculada. Você pode exportar a medição abaixo.")
            elif len(rim_points) == 1:
                st.info("Primeira borda registrada. Selecione a borda oposta no mapa.")
            elif len(rim_points) == 2:
                st.warning("Pontos incompatíveis. Reinicie e escolha duas bordas próximas.")

            with st.expander("Como o diâmetro é calculado?"):
                st.markdown(
                    "A distância entre as coordenadas A e B é calculada pela "
                    "**fórmula de haversine**, com o raio médio lunar de 1.737,4 km."
                )
                st.latex(r"d=2R\arcsin\left(\sqrt{\sin^2\frac{\Delta\varphi}{2}+\cos\varphi_1\cos\varphi_2\sin^2\frac{\Delta\lambda}{2}}\right)")
                st.latex(r"A_{\mathrm{circular}}\approx\pi\left(\frac{d}{2}\right)^2")
                st.caption(
                    "É uma estimativa geométrica. A borda foi escolhida visualmente, "
                    "o diâmetro supõe duas extremidades opostas e a área supõe "
                    "uma formação circular. Não calcula a profundidade."
                )
                st.markdown(
                    "[Raio lunar de referência · NASA](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html)"
                )
            if crater_estimate is not None:
                measurement = {
                    "borda_a_lat": rim_points[0][0],
                    "borda_a_lon_leste": rim_points[0][1],
                    "borda_b_lat": rim_points[1][0],
                    "borda_b_lon_leste": rim_points[1][1],
                    "diametro_aproximado_km": crater_estimate.diameter_km,
                    "raio_aproximado_km": crater_estimate.radius_km,
                    "area_circular_estimada_km2": crater_estimate.area_km2,
                    "centro_estimado_lat": crater_estimate.midpoint[0],
                    "centro_estimado_lon_leste": crater_estimate.midpoint[1],
                    "raio_lua_adotado_km": MOON_RADIUS_KM,
                    "modelo": "haversine e disco circular ideal; bordas selecionadas manualmente",
                }
                st.download_button(
                    "Baixar esta medição (CSV)",
                    data=pd.DataFrame([measurement]).to_csv(index=False).encode("utf-8-sig"),
                    file_name="medicao_cratera_lunar.csv", mime="text/csv",
                    key="crater_measure_csv",
                    use_container_width=True,
                )
        else:
            st.markdown("**02 — Localização do ponto**")
            st.metric("Latitude", f"{lat:+.5f}°")
            st.metric("Longitude leste", f"{lon:+.5f}°")
            st.info(
                "Identificação geográfica: **somente coordenadas**. "
                "Nenhum nome de formação lunar é atribuído automaticamente."
            )
            with st.expander("Informar coordenadas manualmente"):
                origin = (round(lat, 5), round(lon, 5))
                if st.session_state.get("lunar_manual_origin") != origin:
                    st.session_state["lunar_manual_lat"] = lat
                    st.session_state["lunar_manual_lon"] = lon
                    st.session_state["lunar_manual_origin"] = origin
                with st.form("manual_lunar_coords"):
                    st.number_input(
                        "Latitude norte (+) / sul (-)", -90.0, 90.0, lat,
                        step=0.01, format="%.5f", key="lunar_manual_lat",
                    )
                    st.number_input(
                        "Longitude leste (+) / oeste (-)", -180.0, 180.0, lon,
                        step=0.01, format="%.5f", key="lunar_manual_lon",
                    )
                    st.form_submit_button(
                        "Aplicar coordenadas", use_container_width=True,
                        on_click=_apply_manual_coordinates,
                    )
        st.markdown(
            f"[Verificar a região no mapa original NASA Moon Trek]({MOON_TREK})"
        )

    st.markdown("**03 — Coleta de dados para as coordenadas escolhidas**")
    st.caption(
        "A consulta busca posições e distâncias astronômicas do Sol e da Terra, "
        "calculadas pelo JPL para o ponto e o período definidos. "
        "Não mede profundidade nem diâmetro de crateras."
    )
    collect_key = (round(lat, 5), round(lon, 5),
                   start.isoformat(), stop.isoformat(), int(step))
    if st.button(
        "Coletar dados NASA/JPL do ponto", type="primary",
        use_container_width=True, key="collect_lunar_site",
    ):
        try:
            with st.spinner("Consultando efemérides do JPL Horizons para as coordenadas..."):
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
        st.caption("Nenhuma efeméride fictícia será apresentada.")

    meta = {
        "instrumento_cartografico": "LRO Wide Angle Camera; NASA Moon Trek",
        "mapa_wmts": NASA_WAC_TILES,
        "identificacao": "coordenadas apenas — nomes não atribuídos",
        "lat_graus": lat, "lon_leste_graus": lon,
        "periodo_inicio_utc": start.isoformat(),
        "periodo_fim_utc": stop.isoformat(),
        "passo_horas": int(step),
        "fonte_efemerides": "NASA/JPL Horizons",
        "estado_efemerides": "não consultado",
        "nota_cientifica": (
            "Fotografias LRO não fornecem profundidade por si só; "
            "sem modelo de elevação, nenhum valor de altitude é calculado."
        ),
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
            a, b, c, d = st.columns(4)
            a.metric("Sol · elevação", f"{sample['sun_elev']:.2f}°")
            b.metric("Terra · elevação", f"{sample['earth_elev']:.2f}°")
            c.metric("Distância à Terra", f"{sample['earth_dist_km']:,.0f} km")
            d.metric("Luz até a Terra", f"{sample['retardo_terra_s']:.2f} s")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=computed["instante_utc"], y=computed["sun_elev"],
                name="Sol", line=dict(color="#f1d7a8", width=2.5),
            ))
            fig.add_trace(go.Scatter(
                x=computed["instante_utc"], y=computed["earth_elev"],
                name="Terra", line=dict(color="#75b6ed", width=2.5),
            ))
            fig.add_hline(y=0, line_color="#9aaabe", line_dash="dot")
            fig.update_layout(
                template="plotly_dark", height=360,
                paper_bgcolor="#05080e", plot_bgcolor="#05080e",
                xaxis_title="Data e hora (UTC)",
                yaxis_title="Elevação (°)",
                margin=dict(l=10, r=10, t=10, b=30),
                legend=dict(orientation="h"),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(computed, hide_index=True, use_container_width=True)
            st.download_button(
                "Baixar efemérides e cálculos (CSV)",
                data=computed.to_csv(index=False).encode("utf-8-sig"),
                file_name="ponto_lunar_efemerides.csv",
                mime="text/csv", key="lunar_site_csv",
            )
            st.caption(
                "Efemérides/distâncias: JPL; atraso da luz/energia: modelos matemáticos. "
                "Não considera sombras causadas pelo relevo."
            )
        except (ValueError, KeyError, TypeError) as exc:
            st.error(f"Não foi possível interpretar os dados: {str(exc)[:220]}.")
            meta["estado_efemerides"] = "falha de interpretação"

    st.download_button(
        "Baixar ficha de coordenadas e proveniência (JSON)",
        data=json.dumps(meta, ensure_ascii=False, indent=2).encode("utf-8"),
        file_name="ponto_lunar.json",
        mime="application/json", key="lunar_site_json",
    )
    st.caption(
        "Para investigar topografia real, consulte o NASA Moon Trek. "
        "Os perfis de altitude ainda não são importados automaticamente."
    )
