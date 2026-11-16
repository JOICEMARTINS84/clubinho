"""Horizonte Científico — laboratório lunar de efemérides e energia solar."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from horizons import HorizonsError, get_ephemerides
from physics import IRRADIANCIA_REFERENCIA_W_M2, add_solar_power
from craters import render_crater_lab
from lunar_explorer import render_lunar_explorer

st.set_page_config(page_title="Horizonte Científico | Lua", page_icon="🌘", layout="wide")

BG, PANEL, BORDER = "#05080e", "#0c1420", "#263248"
SOL, TERRA, TEXTO = "#f5d8a4", "#74b8f6", "#f2f5fb"

st.markdown("""
<style>
:root { color-scheme: dark; }
html, body, .stApp { background:#05080e !important; color:#f4f6fa; }
[data-testid="stAppViewContainer"] { background:#05080e; }
[data-testid="stMainBlockContainer"] {padding-top:1.25rem;max-width:1500px;}
[data-testid="stSidebar"]{background:#0b1019;border-right:1px solid #252e3c;}
[data-testid="stSidebar"] h3 {font-size:1rem!important;letter-spacing:.015em;}
[data-testid="stSidebar"] label {color:#aeb9c8;}
[data-testid="stSidebar"] [data-testid="stButton"] button {
 background:#f13b2d!important;color:white!important;
 border:0!important;border-radius:3px!important;
 font-size:.9rem!important;font-weight:750!important;
 text-transform:uppercase;letter-spacing:.07em;
 min-height:2.9rem;
}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover{background:#d92c1f!important;}
[data-testid="stMetric"]{
 background:transparent !important; padding:14px 13px 10px;
 border:0!important;border-top:2px solid #263248!important;
 border-radius:0!important;box-shadow:none!important;
}
[data-testid="stMetricLabel"]{color:#9da9b8!important;font-size:.77rem!important;letter-spacing:.015em;}
[data-testid="stMetricValue"]{color:#fcfcff!important;font-variant-numeric:tabular-nums;font-weight:650!important;}
[data-testid="stMetricDelta"]{color:#c1cedc!important;}
h1,h2,h3{font-family:Arial,"Helvetica Neue",sans-serif!important;color:#f9f9fc!important;letter-spacing:-.025em;}
h2{font-size:1.45rem!important;}
h3{font-size:1.12rem!important;}
a{color:#93b9ef!important;text-decoration:none!important;}
a:hover{text-decoration:underline!important;}
hr{border-color:#263044!important;}
[data-testid="stAlert"]{border-radius:4px!important;}
.hero{
 position:relative;overflow:hidden;display:flex;align-items:center;
 min-height:405px;padding:54px clamp(28px,5vw,72px);
 background-color:#05070b;
 background-image:linear-gradient(90deg,#05070c 2%,rgba(5,7,12,.98) 29%,rgba(5,7,12,.74) 54%,rgba(5,7,12,.06) 100%),
 url("https://assets.science.nasa.gov/dynamicimage/assets/science/psd/photojournal/pia/pia13/pia13523/PIA13523.jpg?fit=cover&w=1100&h=1100");
 background-repeat:no-repeat;background-position:center,right 24% center;
 background-size:cover, auto 135%;
 border:1px solid #202b3e;border-radius:2px;
 margin:0 0 7px;
}
.hero-content {position:relative;z-index:1;max-width:680px;}
.mission-name{font-size:.79rem;font-weight:800;letter-spacing:.20em;text-transform:uppercase;color:#f1f4f9;}
.mission-name:before{content:"";display:inline-block;width:27px;height:3px;background:#f13b2d;margin-right:12px;vertical-align:middle;}
.hero h1{font-size:clamp(2.55rem,5.9vw,5.5rem)!important;line-height:.98!important;
 letter-spacing:-.055em!important;font-weight:850!important;margin:28px 0 19px!important;}
.hero h1 span{color:#f13b2d!important;}
.hero p{font-size:1.075rem;line-height:1.55;color:#d4dce8;max-width:540px;}
.hero-meta{display:flex;gap:22px;margin-top:29px;flex-wrap:wrap;
 font-size:.75rem;letter-spacing:.045em;color:#b8c5d8;font-weight:700;}
.hero-meta b{color:#f13b2d;}
.photo-credit{color:#778599!important;font-size:.71rem;margin:0 0 24px;}
.mission-header{border-bottom:1px solid #263246;display:flex;
 justify-content:space-between;gap:14px;flex-wrap:wrap;align-items:baseline;
 padding:0 0 12px;margin:24px 0 9px;}
.mission-header b{font-size:.81rem;letter-spacing:.15em;text-transform:uppercase;color:#edf2fb;}
.mission-header span{font-size:.78rem;color:#8e9caf;letter-spacing:.04em;}
.kicker{font-size:.73rem;letter-spacing:.16em;font-weight:800;text-transform:uppercase;color:#d0d8e6;}
.method-note{border-left:3px solid #f13b2d;padding:13px 18px;
 background:#0d1521;font-size:.9rem;color:#c5d0df;line-height:1.6;border-radius:0;}
div[data-baseweb="tab-list"]{gap:0;border-bottom:1px solid #2a3445;overflow-x:auto;}
button[data-baseweb="tab"]{border-radius:0!important;border:0!important;
 border-bottom:2px solid transparent!important;background:transparent!important;
 color:#a7b5c7!important;font-size:.86rem!important;padding:12px 14px!important;}
button[data-baseweb="tab"][aria-selected="true"]{
 border-bottom-color:#f13b2d!important;color:#fff!important;background:#0c1420!important;}
[data-testid="stDataFrame"]{border:1px solid #28364a;}
@media(max-width:800px){
 .hero{min-height:350px;padding:30px 21px;background-image:
 linear-gradient(90deg,#05070c 0%,rgba(5,7,12,.9) 64%,rgba(5,7,12,.58) 100%),
 url("https://assets.science.nasa.gov/dynamicimage/assets/science/psd/photojournal/pia/pia13/pia13523/PIA13523.jpg?fit=cover&w=760&h=760");
 background-size:cover,auto 100%;background-position:center,right center;}
 .hero h1{font-size:clamp(2.35rem,9vw,3.4rem)!important;}
 .hero-meta{gap:10px;}
}

/* Painel de controle lateral — visual de console educativo */
[data-testid="stSidebar"]{min-width:325px!important;max-width:395px!important;}
[data-testid="stSidebar"] > div:first-child{padding-top:0.4rem!important;}
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="input"] > div {
 background:#101a28!important; border-color:#334057!important;
 border-radius:5px!important; min-height:39px;
}
[data-testid="stSidebar"] [data-testid="stSlider"]{padding:1px 2px 10px;}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"]{color:#d9e0ed!important;}
.side-console{background:linear-gradient(145deg,#18263b,#0a1220);
 border:1px solid #354866;border-top:3px solid #f13b2d;
 padding:19px 16px 15px;margin:0 0 14px;border-radius:3px;}
.side-console-tag{color:#92a8c3;font-size:.66rem;letter-spacing:.18em;font-weight:800;}
.side-console-name{color:#fff;font-size:1.43rem;font-weight:800;
 letter-spacing:-.03em;margin:9px 0 12px;}
.side-console-status{display:flex;align-items:center;gap:9px;font-size:.71rem;
 letter-spacing:.085em;color:#c7d5e8;font-weight:700;}
.indicator{width:8px;height:8px;display:inline-block;background:#9dd9af;
 box-shadow:0 0 10px #56b87988;border-radius:50%;}
.side-step{border-top:1px solid #2b3b52;margin:19px 0 12px;padding-top:16px;
 display:flex;align-items:center;gap:12px;}
.side-step b{width:34px;height:31px;display:flex;align-items:center;justify-content:center;
 background:#f13b2d;color:#fff;font-weight:800;font-size:.8rem;border-radius:2px;}
.side-step span{font-size:.77rem;color:#dfe6f1;letter-spacing:.095em;font-weight:800;}
.coordinate-box,.side-readout{display:flex;justify-content:space-between;flex-wrap:wrap;
 gap:8px;background:#0e1826;border:1px solid #25344a;padding:11px;
 margin:8px 0;font-size:.72rem;color:#9eb1ca;letter-spacing:.025em;}
.coordinate-box span,.side-readout span{display:flex;flex-direction:column;gap:3px;}
.coordinate-box b,.side-readout b{color:#eef2fb;font-family:monospace;font-size:.85rem;}
.side-readout{margin:14px 0 4px;}
@media(max-width:800px){
 [data-testid="stSidebar"]{min-width:0!important;max-width:100%!important;}
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
 <div class="hero-content">
  <div class="mission-name">Matemática &amp; Contexto · Exploração científica</div>
  <h1>HORIZONTE<br><span>LUNAR</span></h1>
  <p>Explore o céu da Lua com efemérides astronômicas do JPL e investigue as condições de iluminação, energia e comunicação.</p>
  <div class="hero-meta"><span><b>01</b> NASA/JPL HORIZONS</span><span><b>02</b> DADOS ASTRONÔMICOS</span><span><b>03</b> ANÁLISE LUNAR</span></div>
 </div>
</div>
""", unsafe_allow_html=True)
st.markdown('<p class="photo-credit">Imagem: mosaico do polo sul lunar · NASA/GSFC/Arizona State University, LRO · PIA13523. Projeto independente, não afiliado à NASA.</p>', unsafe_allow_html=True)

PRESETS = {
    "Definir coordenadas": None,
    "Exemplo A · latitude −89,5°, longitude 0°": (-89.5, 0.0),
    "Exemplo B · latitude −85°, longitude 45°": (-85.0, 45.0),
    "Exemplo C · latitude 0°, longitude 0°": (0.0, 0.0),
}

with st.sidebar:
    status_name = (
        "FALHA NA ÚLTIMA CONSULTA" if st.session_state.get("horizons_error")
        else "DADOS ARMAZENADOS" if "horizons_data" in st.session_state
        else "PRONTO PARA CONSULTA"
    )
    st.markdown(
        '<div class="side-console">'
        '<div class="side-console-tag">ESTAÇÃO DE PESQUISA / HC-01</div>'
        '<div class="side-console-name">Controle de missão</div>'
        f'<div class="side-console-status"><span class="indicator"></span>{status_name}</div>'
        '</div>', unsafe_allow_html=True,
    )
    experience = st.radio(
        "Nível de operação",
        ["Guiado", "Técnico"], horizontal=True, key="mode_experience",
        help="Guiado: controles essenciais e explicações. Técnico: expõe coordenadas e hipóteses completas.",
    )
    st.caption(
        "Guiado: ideal para estudantes. Técnico: parâmetros detalhados para investigação."
        if experience == "Guiado"
        else "Modo técnico: parâmetros de observação e modelo fotovoltaico disponíveis."
    )

    st.caption("Na aba **Explorar e medir**, marque dois pontos na borda de uma cratera para estimar seu diâmetro e sua área.")

    st.markdown('<div class="side-step"><b>01</b><span>LOCAL DE OBSERVAÇÃO</span></div>',
                unsafe_allow_html=True)
    place = st.selectbox(
        "Onde vamos observar?", list(PRESETS), key="study_location",
        help="O local é um ponto de observação imaginário na superfície da Lua.",
    )
    if PRESETS[place] is None:
        lat = st.number_input("Latitude lunar (°)", min_value=-90.0, max_value=90.0,
                              value=-89.5, step=0.1, help="Latitude sul é negativa.")
        lon = st.number_input("Longitude leste (°)", min_value=-180.0, max_value=180.0,
                              value=0.0, step=1.0, help="Longitude leste positiva.")
    else:
        lat, lon = PRESETS[place]
    st.markdown(
        f'<div class="coordinate-box"><span>LATITUDE <b>{lat:+.4f}°</b></span>'
        f'<span>LONGITUDE <b>{lon:+.4f}°</b></span></div>',
        unsafe_allow_html=True,
    )
    st.caption("Este é o ponto a partir do qual o JPL calculará onde o Sol e a Terra aparecem. Nenhuma formação geológica é identificada.")

    st.markdown('<div class="side-step"><b>02</b><span>PERÍODO E RESOLUÇÃO</span></div>',
                unsafe_allow_html=True)
    day = st.date_input(
        "Quando começa a investigação? (UTC)",
        value=datetime.now(timezone.utc).date(),
        min_value=datetime(1900,1,1).date(),
        max_value=datetime(2099,12,31).date(),
        help="A NASA calcula posições astronômicas para a data selecionada; não é uma câmera ao vivo.",
    )
    days = st.slider("Quantos dias vamos estudar?", 1, 14, 7,
                      help="Intervalo total, de 1 até 14 dias.")
    if experience == "Guiado":
        step = 3
        st.caption("Resolução: uma amostra a cada 3 horas (configuração guiada).")
    else:
        step = st.select_slider("Intervalo entre medições calculadas",
                                options=[1,3,6,12], value=3,
                                format_func=lambda v: f"{v} h",
                                help="Intervalos menores dão mais detalhes, mas geram mais linhas na consulta.")
        st.caption("O horário adotado é UTC. Resolução temporal não corresponde a precisão espacial.")

    st.markdown('<div class="side-step"><b>03</b><span>EXPERIMENTO SOLAR</span></div>',
                unsafe_allow_html=True)
    if experience == "Guiado":
        area = st.slider("Tamanho do painel (m²)", 1.0, 12.0, 4.0, 0.5,
                         help="Área útil de células fotovoltaicas: mais área tende a gerar mais potência.")
        efficiency = 22
        mode = st.selectbox("Posição do painel",
                            ["Horizontal", "Rastreamento ideal"],
                            help="Horizontal: painel paralelo ao solo. Rastreamento ideal: painel sempre apontado ao Sol quando visível.")
        tilt, az_panel = 0.0, 0.0
        st.caption("Eficiência adotada: 22% (hipótese de ensino). "
                   "Energia é calculada; não existe sensor nem painel real conectado.")
    else:
        area = st.slider("Área fotovoltaica (m²)", 0.5, 30.0, 4.0, 0.5,
                         help="Área geométrica das células no modelo.")
        efficiency = st.slider("Eficiência elétrica (%)", 5, 35, 22,
                               help="Fração idealizada da irradiância convertida em eletricidade.")
        mode = st.selectbox("Geometria do painel",
                            ["Horizontal","Inclinado fixo","Rastreamento ideal"],
                            help="O rastreamento perfeito é um limite superior idealizado.")
        tilt, az_panel = 0.0, 0.0
        if mode == "Inclinado fixo":
            tilt = st.slider("Inclinação sobre o solo (°)", 0,90,75,
                             help="0° é horizontal; 90° é vertical.")
            az_panel = st.slider("Azimute frontal do painel (°)", 0,359,180,
                                 help="Direção da normal projetada: 0° norte, 90° leste.")
        st.caption("Hipótese matemática: perdas térmicas, poeira e relevo ainda não entram no cálculo.")

    st.markdown('<div class="side-step"><b>04</b><span>EXECUTAR INVESTIGAÇÃO</span></div>',
                unsafe_allow_html=True)
    st.caption("Envia coordenadas e datas ao JPL Horizons. O processamento físico acontece em Python.")
    load = st.button("▶  Executar análise lunar", type="primary",
                     use_container_width=True, key="run_horizons")
    st.markdown(
        '<div class="side-readout"><span>FONTE <b>JPL HORIZONS</b></span>'
        '<span>ESCALA <b>UTC</b></span>'
        '<span>ESTADO <b>CONSULTA SOB DEMANDA</b></span></div>',
        unsafe_allow_html=True,
    )
    with st.expander("Guia rápido: o que significa cada resultado?"):
        st.markdown(
            "**Elevação:** altura angular do Sol ou da Terra acima do horizonte ideal.\n\n"
            "**Distância:** separação calculada pelo JPL, em quilômetros.\n\n"
            "**Irradiância:** potência solar recebida por área; é uma estimativa física.\n\n"
            "**Energia:** modelo de geração do painel, não medição.\n\n"
            "**Imagem de cratera:** fotografia real que podemos analisar em pixels."
        )
    st.markdown("[Mapas reais e perfis de altitude · NASA Moon Trek](https://trek.nasa.gov/moon/)")


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
        st.session_state["horizons_retrieved"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
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
        st.info("Defina o local e o período na barra lateral e clique em **Executar análise** para consultar as efemérides reais do JPL.")
    st.markdown("""
    <div class="method-note">Módulo astronômico: dados NASA/JPL Horizons. Módulo energético: modelo matemático.
    O relevo observado pelo LRO/LOLA é referência visual, ainda sem correção local de sombras.</div>
    """, unsafe_allow_html=True)
    explorer_tab, atlas_tab, crater_tab = st.tabs(["Explorar e medir", "Atlas NASA/LRO", "Laboratório de crateras"])
    with explorer_tab:
        render_lunar_explorer(start, stop, step, area, efficiency, mode, tilt, az_panel)
    with atlas_tab:
        st.markdown('<div class="mission-header"><b>Cartografia lunar</b><span>LRO / LOLA · REGIÃO POLAR</span></div>', unsafe_allow_html=True)
        st.subheader("Polo sul · dados observacionais NASA/LRO")
        col_img, col_note = st.columns([1, 1], gap="large")
        with col_img:
            try:
                st.image("https://science.nasa.gov/wp-content/uploads/2024/06/psrs-n-topo3.png",
                         caption="NASA/LRO/LOLA — topografia e regiões permanentemente sombreadas.",
                         use_container_width=True)
            except Exception:
                st.caption("A imagem remota da NASA está indisponível.")
        with col_note:
            st.markdown("**Observe dados reais do relevo lunar.** A carta do polo sul mostra "
                        "regiões permanentemente sombreadas sobre uma base topográfica derivada do LRO/LOLA.")
            st.markdown("[Consultar a imagem e os resultados científicos na NASA](https://science.nasa.gov/solar-system/moon/nasas-lro-lunar-ice-deposits-are-widespread/)")
            st.markdown("[Abrir o mapa interativo NASA Moon Trek](https://trek.nasa.gov/moon/)")
            st.caption("Esta cartografia não substitui a consulta ao JPL e não alimenta o cálculo fotovoltaico.")
    with crater_tab:
        render_crater_lab()
    st.stop()

raw = st.session_state["horizons_data"]
df = add_solar_power(raw, area, efficiency, mode, tilt, az_panel)

n = len(df)
sun_fraction = 100 * (df["sun_elev"] > 0).mean()
earth_fraction = 100 * (df["earth_elev"] > 0).mean()
energy = df["energia_acumulada_kwh"].iloc[-1]
max_power = df["potencia_w"].max()

st.markdown('<div class="mission-header"><b>Resultados da investigação</b><span>EFEMÉRIDES / VISIBILIDADE / ENERGIA</span></div>', unsafe_allow_html=True)
st.caption(f"JPL Horizons · {n} amostras UTC · horizonte geométrico 0° · {lat:.2f}° lat., {lon:.2f}° long.")
st.caption(f"Consulta executada em UTC: {st.session_state.get('horizons_retrieved', 'não registrado')} · "
           f"período modelado: {start:%d/%m/%Y} a {stop:%d/%m/%Y}")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Sol visível · amostras", f"{sun_fraction:.0f}%", help="Fração das amostras com elevação solar > 0°. Não é porcentagem temporal contínua.")
c2.metric("Terra visível · amostras", f"{earth_fraction:.0f}%", help="Fração das amostras com elevação terrestre > 0°. Não modela montanhas nem comunicação por rádio.")
c3.metric("Energia · modelo", f"{energy:.2f} kWh", help="Energia fotovoltaica hipotética integrada a partir de irradiância por distância.")
c4.metric("Potência máxima · modelo", f"{max_power:.0f} W", help="Máxima potência calculada no intervalo amostrado.")
first = df.iloc[0]
st.markdown('<div class="mission-header"><b>Dados de referência</b><span>PRIMEIRA AMOSTRA DO INTERVALO · JPL</span></div>', unsafe_allow_html=True)
d1, d2, d3, d4 = st.columns(4)
d1.metric("Distância à Terra", f"{first['earth_dist_km']:,.0f} km", help="Distância do observador lunar ao centro da Terra · JPL Horizons.")
d2.metric("Distância ao Sol", f"{first['sun_dist_km']/1e6:,.3f} milhões km", help="Distância do observador lunar ao Sol · JPL Horizons.")
d3.metric("Luz até a Terra", f"{first['retardo_terra_s']:.2f} s", help="Estimativa da distância ao centro da Terra dividida pela velocidade da luz.")
d4.metric("Separação Sol–Terra", f"{first['separacao_sol_terra_deg']:.1f}°", help="Separação angular calculada a partir de azimutes e elevações topocêntricos.")


def style_chart(fig, height=415):
    fig.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(color=TEXTO, size=13), margin=dict(l=15, r=15, t=34, b=15),
        height=height, legend=dict(orientation="h", y=1.11, x=0),
        hovermode="x unified",
    )
    return fig


explorer_tab, v, distances, power, sky, topo, craters_tab, method = st.tabs(["Explorar e medir", "Visão orbital", "Distâncias", "Energia", "Céu lunar", "Topografia", "Analisar crateras", "Método científico"])
with explorer_tab:
    render_lunar_explorer(start, stop, step, area, efficiency, mode, tilt, az_panel)
with v:
    st.subheader("Elevação dos astros · JPL Horizons")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["instante_utc"], y=df["sun_elev"], name="Sol", mode="lines+markers",
                             line=dict(color=SOL, width=2.8), marker=dict(size=4)))
    fig.add_trace(go.Scatter(x=df["instante_utc"], y=df["earth_elev"], name="Terra", mode="lines+markers",
                             line=dict(color=TERRA, width=2.4), marker=dict(size=4)))
    fig.add_hline(y=0, line_width=1.2, line_dash="dash", line_color="#8793a7")
    fig.update_yaxes(title="Elevação aparente (graus)", zeroline=False, gridcolor="#303036")
    fig.update_xaxes(title="Data e hora (UTC)", gridcolor="#29292e")
    st.plotly_chart(style_chart(fig), use_container_width=True)
    st.caption("Elevações topocêntricas em graus. Não considera crateras, montanhas ou obstáculos artificiais.")
    st.markdown("**Separação angular Sol–Terra** · calculada das duas direções observadas")
    sep_plot = go.Figure()
    sep_plot.add_trace(go.Scatter(x=df["instante_utc"], y=df["separacao_sol_terra_deg"],
                                  name="Separação angular", mode="lines",
                                  line=dict(color="#d4a27f", width=2.6)))
    sep_plot.update_yaxes(title="Ângulo (°)", range=[0,180])
    sep_plot.update_xaxes(title="Data e hora (UTC)")
    st.plotly_chart(style_chart(sep_plot, 275), use_container_width=True)

with distances:
    st.subheader("Distâncias aparentes · JPL Horizons")
    st.caption("Valores da NASA/JPL ao centro da Terra e ao centro do Sol, vistos do observador lunar.")
    fig_earth = go.Figure()
    fig_earth.add_trace(go.Scatter(x=df["instante_utc"], y=df["earth_dist_km"],
                                   name="Distância à Terra", line=dict(color=TERRA, width=2.8)))
    fig_earth.update_yaxes(title="Distância à Terra (km)")
    fig_earth.update_xaxes(title="Data e hora (UTC)")
    st.plotly_chart(style_chart(fig_earth, 340), use_container_width=True)
    fig_sun = go.Figure()
    fig_sun.add_trace(go.Scatter(x=df["instante_utc"], y=df["sun_dist_km"]/1e6,
                                 name="Distância ao Sol", line=dict(color=SOL, width=2.8)))
    fig_sun.update_yaxes(title="Distância ao Sol (milhões de km)")
    fig_sun.update_xaxes(title="Data e hora (UTC)")
    st.plotly_chart(style_chart(fig_sun, 310), use_container_width=True)
    fig_delay = go.Figure()
    fig_delay.add_trace(go.Scatter(x=df["instante_utc"], y=df["retardo_terra_s"],
                                   name="Tempo estimado de propagação",
                                   line=dict(color="#a8cbbf", width=2.8)))
    fig_delay.update_yaxes(title="Tempo estimado (segundos)")
    fig_delay.update_xaxes(title="Data e hora (UTC)")
    st.plotly_chart(style_chart(fig_delay, 290), use_container_width=True)
    st.caption("Distância à Terra dividida pela velocidade da luz. "
               "Não inclui equipamentos, enlaces intermediários nem sombras de montanhas.")

with power:
    st.subheader("Energia solar calculada")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["instante_utc"], y=df["potencia_w"], name="Potência estimada",
                             mode="lines", fill="tozeroy", line=dict(color=SOL, width=3),
                             fillcolor="rgba(231,187,117,0.16)"))
    fig.update_yaxes(title="Potência elétrica (W)", gridcolor="#303036")
    fig.update_xaxes(title="Data e hora (UTC)", gridcolor="#29292e")
    st.plotly_chart(style_chart(fig), use_container_width=True)
    st.latex(r"S(r)=1361\left(\frac{1\,\mathrm{UA}}{r}\right)^2\qquad P(t)=S(r)\,A\,\eta\,\max(0,\cos\theta(t))")
    st.caption(f"1361 W/m² a 1 UA (referência); distância solar conforme o JPL; área = {area:.1f} m²; "
               f"eficiência = {efficiency}%; orientação: {mode}. Não é geração de energia medida.")
    st.markdown("**Irradiância solar no ponto lunar · modelo físico**")
    flux = go.Figure()
    flux.add_trace(go.Scatter(x=df["instante_utc"], y=df["irradiancia_estim_w_m2"],
                              name="Irradiância por distância", line=dict(color="#deb980", width=2.7)))
    flux.update_yaxes(title="Irradiância calculada (W/m²)")
    flux.update_xaxes(title="Data e hora (UTC)")
    st.plotly_chart(style_chart(flux, 315), use_container_width=True)
    st.caption("A irradiância varia pela distância Sol–Lua fornecida pelo JPL e pela lei do inverso do quadrado. "
               "É uma estimativa de fluxo no vácuo, não uma medição de sensor.")
    st.info("O modelo ignora sombras do terreno, poeira, perdas térmicas, envelhecimento, bateria, "
            "eletrônica e indisponibilidade por manutenção. Rastreamento ideal supõe o painel sempre perpendicular "
            "aos raios solares quando o Sol está acima de 0°.")

with sky:
    st.subheader("Projeção polar · céu local da Lua")
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
    az1, az2 = st.columns(2)
    az1.metric("Sol · azimute / elevação", f"{selected['sun_az']:.1f}° / {selected['sun_elev']:.1f}°")
    az2.metric("Terra · azimute / elevação", f"{selected['earth_az']:.1f}° / {selected['earth_elev']:.1f}°")
    st.caption("Azimute: norte 0°, leste 90°, sul 180°, oeste 270°. "
               "A projeção mostra apenas direções; não é um mapa de terreno.")

with topo:
    st.subheader("Polo sul lunar · cartografia real")
    st.caption("Produto visual NASA/LRO/LOLA: topografia regional e regiões permanentemente sombreadas.")
    try:
        st.image("https://science.nasa.gov/wp-content/uploads/2024/06/psrs-n-topo3.png",
                 caption="NASA/LRO — topografia regional do polo sul (LOLA). Áreas azuis: regiões permanentemente sombreadas mapeadas.",
                 use_container_width=True)
    except Exception:
        st.warning("A imagem da NASA não pôde ser carregada neste momento. Abra a fonte abaixo.")
    st.markdown("[Ver pesquisa e imagem original na NASA](https://science.nasa.gov/solar-system/moon/nasas-lro-lunar-ice-deposits-are-widespread/)")
    st.markdown("[Explorar relevo, imagens e camadas no NASA Moon Trek](https://trek.nasa.gov/moon/)")
    st.info("O mapa é um dado cartográfico real da região polar. Nesta versão, o modelo de energia "
            "não utiliza a altitude de cada pixel nem as sombras para corrigir os cálculos do ponto selecionado.")

with craters_tab:
    render_crater_lab()

with method:
    st.subheader("Procedência e limites científicos")
    st.markdown("""
    **Fonte das posições astronômicas:** NASA/JPL Horizons, API pública, efemérides
    do tipo `OBSERVER`, origem `coord@301` (Lua), alvos `10` (Sol) e `399` (Terra),
    quantidades `4,20` (azimute/elevação e distância), `RANGE_UNITS=KM`, UTC.

    **Coordenadas:** latitude geodética informada pelo usuário, longitude positiva a leste
    e altitude adotada de 0 km no elipsoide lunar. Os exemplos numéricos são pontos
    de estudo sem identificação de crateras ou outros nomes geográficos.

    **Critério visual:** elevação do centro do astro superior a 0°. Não considera o
    tamanho angular do disco, sombras produzidas pelo relevo ou obstáculos artificiais.

    **Modelo fotovoltaico:** irradiância de referência de 1361 W/m² a uma unidade astronômica.
    Irradiância local calculada pela lei inversa do quadrado da distância solar obtida do JPL.
    Potência calculada com a geometria do painel, área e eficiência hipotética.
    Energia estimada por integração trapezoidal das amostras. Esses resultados não são
    medições de um painel solar nem previsões de engenharia.

    **Comunicação:** tempo de propagação aproximado = distância aparente à Terra dividida
    pela velocidade da luz no vácuo. Não calcula perdas, alinhamento nem disponibilidade do rádio.

    **Visibilidade:** percentuais mostram a proporção das amostras com elevação positiva,
    e não a fração exata de tempo. As mudanças de visibilidade entre amostras não são resolvidas.

    **Medição geométrica de crateras:** na aba Explorar e medir, a distância
    superficial entre duas bordas escolhidas usa haversine e raio lunar médio
    de 1737,4 km (NASA). A área estimada é a de um círculo ideal de diâmetro
    igual à distância. Não identifica bordas automaticamente, não mede altitude
    nem calcula profundidade.

    **Próxima etapa:** incorporar mapa de elevação LOLA/LRO para calcular
    a linha real do horizonte em cada azimute.
    """)
    st.markdown("[Documentação do JPL Horizons](https://ssd-api.jpl.nasa.gov/doc/horizons.html) · "
                "[NASA Moon Trek · mapas reais](https://trek.nasa.gov/moon/) · "
                "[LRO/LOLA · altimetria](https://pds-geosciences.wustl.edu/missions/lro/lola.htm)")
    st.info("Moon Trek oferece mapas lunares reais, mas ainda não importamos seus dados de "
            "elevação para calcular a linha local do horizonte. Nenhuma sombra de crateras é simulada.")
    display = df.rename(columns={
        "instante_utc": "Data/hora UTC", "sun_az": "Azimute Sol (°)", "sun_elev": "Elevação Sol (°)",
        "earth_az": "Azimute Terra (°)", "earth_elev": "Elevação Terra (°)",
        "sun_dist_km": "Distância Sol (km)", "earth_dist_km": "Distância Terra (km)",
        "retardo_terra_s": "Luz à Terra (s)", "separacao_sol_terra_deg": "Separação Sol–Terra (°)",
        "irradiancia_estim_w_m2": "Irradiância calculada (W/m²)",
        "incidencia": "Fator de incidência", "potencia_w": "Potência estimada (W)",
        "energia_acumulada_kwh": "Energia estimada (kWh)",
    })
    st.dataframe(display, use_container_width=True, hide_index=True)
    st.download_button("Baixar resultados (CSV)", data=display.to_csv(index=False).encode("utf-8-sig"),
                       file_name="horizonte_cientifico_lunar.csv", mime="text/csv")
    protocolo = {
        "projeto": "Horizonte Científico / Lua",
        "autora": "Joice Souza Martins Santos",
        "consulta_utc": st.session_state.get("horizons_retrieved"),
        "fonte": "NASA/JPL Horizons",
        "api": "https://ssd.jpl.nasa.gov/api/horizons.api",
        "observador": "coord@301; GEODETIC; altitude=0 km",
        "alvos": {"sun": "10", "earth": "399"},
        "quantidades": "4,20",
        "unidades_range": "km",
        "latitude": float(lat), "longitude_leste": float(lon),
        "data_inicio_utc": start.isoformat(),
        "data_fim_utc": stop.isoformat(),
        "amostragem_horas": int(step),
        "amostras": int(n),
        "modelo": {
            "irradiancia_referencia_w_m2": IRRADIANCIA_REFERENCIA_W_M2,
            "potencia": "lei inversa do quadrado + area + eficiencia + incidencia",
            "area_m2": float(area), "eficiencia_pct": int(efficiency),
            "orientacao": mode, "inclinacao_graus": float(tilt),
            "azimute_painel_graus": float(az_panel),
            "horizonte": "geometrico, sem obstrucao por relevo",
        },
    }
    st.download_button("Baixar protocolo da consulta (JSON)",
                       data=json.dumps(protocolo, ensure_ascii=False, indent=2).encode("utf-8"),
                       file_name="horizonte_lunar_protocolo.json", mime="application/json")

st.divider()
st.caption("Matemática & Contexto · Joice Souza Martins Santos · versão 2.0 · Efemérides JPL e modelos físicos identificados")
