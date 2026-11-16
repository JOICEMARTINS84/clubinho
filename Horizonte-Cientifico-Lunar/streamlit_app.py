"""Horizonte Científico — laboratório lunar de efemérides e energia solar."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from horizons import HorizonsError, get_ephemerides
from physics import IRRADIANCIA_REFERENCIA_W_M2, add_solar_power

st.set_page_config(page_title="Horizonte Científico | Lua", page_icon="🌘", layout="wide")

BG, PANEL, BORDER = "#101014", "#1b1b20", "#3a3936"
SOL, TERRA, TEXTO = "#e7bb75", "#d6d5d1", "#f5f2eb"

st.markdown("""
<style>
:root {color-scheme: dark;}
.stApp {background: #101014; color: #f5f2eb;}
[data-testid="stSidebar"] {background: #19191d; border-right: 1px solid #39393d;}
[data-testid="stMetric"] {background: #1d1d21; border: 1px solid #38383b; padding: 16px; border-radius: 12px;}
[data-testid="stMetricLabel"] {color: #c8c2b8;}
h1,h2,h3 {color: #f6f1e7 !important;}
.hero {padding: 28px 30px; border: 1px solid #4c4235; border-radius: 16px;
       background: linear-gradient(110deg, #27231e 0%, #17171a 65%, #101014 100%);
       margin: 6px 0 24px 0;}
.hero h1 {font-size: clamp(1.7rem, 3.3vw, 3rem); margin: 0 0 6px 0 !important;}
.hero p {color: #d0c6b7; margin: 0; font-size: 1.05rem;}
.eyebrow {font-size: .73rem; font-weight: 700; letter-spacing: .2em; color: #e8bd80; margin-bottom: 8px;}
.method-note {padding: 12px 16px; background: #1e1d1c; border-left: 3px solid #c99d67;
              color: #dcd7ce; border-radius: 4px; font-size: .92rem;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="eyebrow">MATEMÁTICA &amp; CONTEXTO · LABORATÓRIO CIENTÍFICO</div>
  <h1>Horizonte Científico <span style="color:#d3aa74">/ Lua</span></h1>
  <p>Explore a geometria do Sol e da Terra no céu lunar e investigue a geração de energia.</p>
</div>
""", unsafe_allow_html=True)

PRESETS = {
    "Polo Sul · exemplo (0°; −89,5°)": (-89.5, 0.0),
    "Sul lunar · exemplo (45°; −85°)": (-85.0, 45.0),
    "Equador lunar · exemplo (0°; 0°)": (0.0, 0.0),
    "Personalizar coordenadas": None,
}

with st.sidebar:
    st.subheader("Local de observação")
    place = st.selectbox("Ponto lunar", list(PRESETS))
    if PRESETS[place] is None:
        lat = st.number_input("Latitude (°)", min_value=-90.0, max_value=90.0, value=-89.5, step=0.1)
        lon = st.number_input("Longitude leste (°)", min_value=-180.0, max_value=180.0, value=0.0, step=1.0)
    else:
        lat, lon = PRESETS[place]
    st.caption(f"Latitude: {lat:.2f}° · Longitude: {lon:.2f}° leste")
    st.divider()
    st.subheader("Período de análise")
    day = st.date_input("Data inicial (UTC)", value=datetime.now(timezone.utc).date(),
                        min_value=datetime(1900, 1, 1).date(), max_value=datetime(2099, 12, 31).date())
    days = st.slider("Duração (dias)", 1, 14, 7)
    step = st.select_slider("Amostragem", options=[3, 6, 12], value=6, format_func=lambda v: f"{v} horas")
    st.divider()
    st.subheader("Painel fotovoltaico · hipótese")
    area = st.slider("Área (m²)", 0.5, 30.0, 4.0, 0.5)
    efficiency = st.slider("Eficiência (%)", 5, 35, 22)
    mode = st.selectbox("Orientação", ["Horizontal", "Inclinado fixo", "Rastreamento ideal"])
    tilt, az_panel = 0.0, 0.0
    if mode == "Inclinado fixo":
        tilt = st.slider("Inclinação desde a horizontal (°)", 0, 90, 75)
        az_panel = st.slider("Direção da face do painel (°)", 0, 359, 180)
    load = st.button("Consultar NASA / JPL", type="primary", use_container_width=True)
    st.caption("Requer internet. Nenhum dado observacional é inventado em caso de falha da API.")

start = datetime.combine(day, datetime.min.time()).replace(tzinfo=timezone.utc)
stop = start + timedelta(days=days)
query_key = (round(float(lat), 6), round(float(lon), 6), start.isoformat(), stop.isoformat(), step)

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_cached(latitude, longitude, since, until, cadence):
    return get_ephemerides(latitude, longitude, since, until, cadence)

if load:
    try:
        with st.spinner("Consultando efemérides topocêntricas do JPL Horizons…"):
            data = fetch_cached(float(lat), float(lon), start, stop, step)
        st.session_state["horizons_data"] = data
        st.session_state["horizons_key"] = query_key
        st.session_state.pop("horizons_error", None)
    except (HorizonsError, ValueError) as exc:
        st.session_state["horizons_error"] = str(exc)
        st.session_state.pop("horizons_data", None)
        st.session_state.pop("horizons_key", None)

if "horizons_error" in st.session_state:
    st.error(st.session_state["horizons_error"])
    st.caption("Verifique a conexão, escolha outra data ou tente novamente. A visualização não substitui dados ausentes por valores fictícios.")

if "horizons_data" not in st.session_state or st.session_state.get("horizons_key") != query_key:
    if "horizons_data" in st.session_state and st.session_state.get("horizons_key") != query_key:
        st.warning("As coordenadas ou datas foram alteradas. Consulte a NASA novamente para atualizar os resultados.")
    else:
        st.info("Escolha as coordenadas e o período na barra lateral. Depois clique em **Consultar NASA / JPL**.")
    st.markdown("""
    <div class="method-note">Primeira versão: posição astronômica do Sol e da Terra calculada pelo JPL Horizons.
    A energia é uma estimativa matemática. Ainda não incorporamos dados de altitude nem sombras de crateras.</div>
    """, unsafe_allow_html=True)
    st.stop()

raw = st.session_state["horizons_data"]
df = add_solar_power(raw, area, efficiency, mode, tilt, az_panel)

n = len(df)
sun_fraction = 100 * (df["sun_elev"] > 0).mean()
earth_fraction = 100 * (df["earth_elev"] > 0).mean()
energy = df["energia_acumulada_kwh"].iloc[-1]
max_power = df["potencia_w"].max()

st.caption(f"DADOS CONSULTADOS · NASA/JPL HORIZONS · {n} instantes UTC · horizonte geométrico de altitude 0°")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Sol acima do horizonte", f"{sun_fraction:.0f}%", help="Percentual das amostras com elevação solar positiva")
c2.metric("Terra acima do horizonte", f"{earth_fraction:.0f}%", help="Percentual das amostras com elevação terrestre positiva")
c3.metric("Energia teórica", f"{energy:.2f} kWh", help="Integração trapezoidal da potência simulada")
c4.metric("Pico de potência", f"{max_power:.0f} W", help="Máxima potência calculada no intervalo amostrado")


def style_chart(fig, height=415):
    fig.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(color=TEXTO, size=13), margin=dict(l=15, r=15, t=34, b=15),
        height=height, legend=dict(orientation="h", y=1.11, x=0),
        hovermode="x unified",
    )
    return fig


v, power, sky, method = st.tabs(["Sol e Terra", "Energia", "Céu local", "Dados e método"])
with v:
    st.subheader("Elevação sobre o horizonte lunar")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["instante_utc"], y=df["sun_elev"], name="Sol", mode="lines+markers",
                             line=dict(color=SOL, width=2.8), marker=dict(size=4)))
    fig.add_trace(go.Scatter(x=df["instante_utc"], y=df["earth_elev"], name="Terra", mode="lines+markers",
                             line=dict(color=TERRA, width=2.4), marker=dict(size=4)))
    fig.add_hline(y=0, line_width=1.2, line_dash="dash", line_color="#9c988f")
    fig.update_yaxes(title="Elevação aparente (graus)", zeroline=False, gridcolor="#303036")
    fig.update_xaxes(title="Data e hora (UTC)", gridcolor="#29292e")
    st.plotly_chart(style_chart(fig), use_container_width=True)
    st.caption("Acima de 0°: astro acima do horizonte geométrico, desconsiderando crateras e montanhas. "
               "Isso não garante iluminação efetiva nem comunicação desobstruída.")

with power:
    st.subheader("Energia solar calculada")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["instante_utc"], y=df["potencia_w"], name="Potência estimada",
                             mode="lines", fill="tozeroy", line=dict(color=SOL, width=3),
                             fillcolor="rgba(231,187,117,0.16)"))
    fig.update_yaxes(title="Potência elétrica (W)", gridcolor="#303036")
    fig.update_xaxes(title="Data e hora (UTC)", gridcolor="#29292e")
    st.plotly_chart(style_chart(fig), use_container_width=True)
    st.latex(r"P(t) = S_0 \, A \, \eta \, \max(0,\cos\theta(t))")
    st.caption(f"S₀ = {IRRADIANCIA_REFERENCIA_W_M2:,.0f} W/m² (referência adotada); A = {area:.1f} m²; "
               f"η = {efficiency}%; orientação: {mode}. O resultado é uma estimativa, não geração medida.")
    st.info("O modelo ignora sombras do terreno, poeira, perdas térmicas, envelhecimento, bateria, "
            "eletrônica e indisponibilidade por manutenção. Rastreamento ideal supõe o painel sempre perpendicular "
            "aos raios solares quando o Sol está acima de 0°.")

with sky:
    st.subheader("Direções no céu em um instante selecionado")
    position = st.slider("Selecione uma amostra", 0, n - 1, 0, format="%d") if n > 1 else 0
    selected = df.iloc[position]
    st.caption(f"Instante UTC: {selected['instante_utc']:%d/%m/%Y %H:%M} · Centro = zênite · Círculo externo = horizonte (0°)")
    polar = go.Figure()
    for target, color, label in (("sun", SOL, "Sol"), ("earth", TERRA, "Terra")):
        alt = float(selected[f"{target}_elev"])
        az = float(selected[f"{target}_az"])
        if alt > 0:
            polar.add_trace(go.Scatterpolar(
                r=[90 - alt], theta=[az], mode="markers+text", text=[label], textposition="top center",
                name=label, marker=dict(color=color, size=15), textfont=dict(color=color, size=15),
                hovertemplate=f"{label}: azimute {az:.2f}°, elevação {alt:.2f}°<extra></extra>"
            ))
        else:
            st.caption(f"{label}: abaixo do horizonte geométrico (azimute {az:.1f}°, elevação {alt:.1f}°).")
    polar.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=BG,
        height=430, margin=dict(t=20, b=20, l=20, r=20), showlegend=True,
        polar=dict(bgcolor=BG, angularaxis=dict(rotation=90, direction="clockwise",
                                                tickmode="array", tickvals=[0,90,180,270],
                                                ticktext=["N", "L", "S", "O"], color=TEXTO),
                   radialaxis=dict(range=[0,90], tickvals=[0,30,60,90], ticktext=["90°", "60°", "30°", "0°"],
                                   gridcolor="#55504a", color="#d3ccc0", angle=45)),
    )
    st.plotly_chart(polar, use_container_width=True)
    st.caption("Azimute medido do norte para leste. A elevação é topocêntrica, referente a uma superfície idealizada.")

with method:
    st.subheader("Procedência e limites científicos")
    st.markdown("""
    **Fonte das posições astronômicas:** NASA/JPL Horizons, API pública, efemérides
    do tipo `OBSERVER`, origem `coord@301` (Lua), alvos `10` (Sol) e `399` (Terra),
    quantidade `4` (azimute/elevação) e instantes UTC.

    **Coordenadas:** planetodéticas, longitude positiva para leste e altitude adotada de
    0 km relativa ao elipsoide de referência da Lua.

    **Critério visual:** elevação do centro do astro superior a 0°. Não considera o
    tamanho angular do disco, sombras produzidas pelo relevo ou obstáculos artificiais.

    **Modelo fotovoltaico:** irradiância de referência constante de 1361 W/m²,
    área e eficiência escolhidas, geometria de incidência conforme a orientação
    do painel e integração trapezoidal do sinal amostrado. A energia não é prevista
    com precisão de engenharia, tampouco medida pela NASA.

    **Próxima etapa:** incorporar mapa de elevação LOLA/LRO para calcular
    a linha real do horizonte em cada azimute.
    """)
    st.markdown("[Documentação do JPL Horizons](https://ssd-api.jpl.nasa.gov/doc/horizons.html) · "
                "[Dados lunares LRO/LOLA](https://pds-geosciences.wustl.edu/missions/lro/lola.htm)")
    display = df.rename(columns={
        "instante_utc": "Data/hora UTC", "sun_az": "Azimute Sol (°)", "sun_elev": "Elevação Sol (°)",
        "earth_az": "Azimute Terra (°)", "earth_elev": "Elevação Terra (°)",
        "incidencia": "Fator de incidência", "potencia_w": "Potência (W)",
        "energia_acumulada_kwh": "Energia acumulada (kWh)",
    })
    st.dataframe(display, use_container_width=True, hide_index=True)
    st.download_button("Baixar resultados (CSV)", data=display.to_csv(index=False).encode("utf-8-sig"),
                       file_name="horizonte_cientifico_lunar.csv", mime="text/csv")

st.divider()
st.caption("Matemática & Contexto · Joice Souza Martins Santos · versão 1.0 · Pesquisa e educação científica")
