"""Horizonte Científico — laboratório lunar de efemérides e energia solar."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from horizons import HorizonsError, get_ephemerides
from physics import IRRADIANCIA_REFERENCIA_W_M2, add_solar_power

st.set_page_config(page_title="Horizonte Científico | Lua", page_icon="🌘", layout="wide")

BG, PANEL, BORDER = "#0b1015", "#14212a", "#324653"
SOL, TERRA, TEXTO = "#e3bd82", "#83c4c4", "#e8eff1"

st.markdown("""
<style>
:root{color-scheme:dark;}
.stApp{background:#0b1015;color:#ecf1f0;}
[data-testid="stSidebar"]{background:#101820;border-right:1px solid #273744;}
[data-testid="stMetric"]{background:linear-gradient(155deg,#16222b,#111920);
 border:1px solid #30414d;padding:19px 18px;border-radius:13px;
 box-shadow:0 8px 26px rgba(0,0,0,.12);}
[data-testid="stMetricLabel"]{color:#a4b8c0;font-size:.87rem;}
[data-testid="stMetricValue"]{color:#f2f5f3;font-variant-numeric:tabular-nums;}
[data-testid="stVerticalBlock"]{gap:.72rem;}
h1,h2,h3{font-family:'Segoe UI',Arial,sans-serif!important;letter-spacing:-.02em;color:#eaf2f2!important;}
hr{border-color:#293946!important;}
a{color:#9dcfc6!important;}
.hero{padding:30px 32px;border:1px solid #44535c;border-left:4px solid #d7b883;border-radius:14px;
 background:radial-gradient(circle at 88% 30%,rgba(153,192,190,.13),transparent 38%),
 linear-gradient(117deg,#1c2830 4%,#101a23 70%,#0b1117);margin:2px 0 19px;}
.hero h1{font-size:clamp(1.8rem,3.5vw,3rem);margin:7px 0 10px!important;line-height:1.17;}
.hero p{color:#b1c4ca;margin:0;font-size:1rem;max-width:700px;}
.eyebrow{font:700 .72rem/1.4 'Segoe UI',sans-serif;letter-spacing:.17em;color:#dfc18f;}
.statusline{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0 0;font-size:.76rem;color:#b4c6c8;}
.statusline span{border:1px solid #45606c;border-radius:4px;padding:5px 10px;background:#14222a;}
.method-note{padding:14px 17px;background:#19232a;border-left:3px solid #d7b883;color:#cbd6d7;border-radius:5px;font-size:.91rem;}
.kicker{color:#d8b781;font-size:.72rem;font-weight:700;letter-spacing:.17em;}
div[data-baseweb="tab-list"]{gap:8px;}
button[data-baseweb="tab"]{background:#14212a;border:1px solid #2d4653;border-radius:8px;padding:9px 15px;color:#d2e1e3;}
button[data-baseweb="tab"][aria-selected="true"]{border-color:#d7b883;color:#f6dfb4;}
@media(max-width:700px){.hero{padding:20px 18px}.hero h1{font-size:1.7rem}}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="eyebrow">OBSERVATÓRIO LUNAR // MATEMÁTICA &amp; CONTEXTO</div>
  <h1>Horizonte Científico <span style="color:#dec39a">/ Lua</span></h1>
  <p>Efemérides topocêntricas, distâncias astronômicas, visibilidade geométrica e geração fotovoltaica estimada.</p>
  <div class="statusline"><span>FONTE: NASA / JPL HORIZONS</span><span>REFERENCIAL: SUPERFÍCIE LUNAR</span><span>ESCALA TEMPORAL: UTC</span></div>
</div>
""", unsafe_allow_html=True)

PRESETS = {
    "Polo Sul · ponto de estudo (89,5°S)": (-89.5, 0.0),
    "Sul lunar · ponto de estudo (85°S)": (-85.0, 45.0),
    "Apollo 11 · Mare Tranquillitatis (NASA)": (0.67416, 23.47314),
    "Apollo 15 · Hadley Rille (NASA)": (26.13239, 3.63330),
    "Apollo 17 · Taurus–Littrow (NASA)": (20.19110, 30.77230),
    "Equador lunar · ponto de estudo": (0.0, 0.0),
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
    st.caption(f"Latitude: {lat:.4f}° · Longitude: {lon:.4f}° leste")
    if "Apollo" in place:
        st.caption("Coordenadas publicadas pela NASA/NSSDC, referencial planetocêntrico, "
                   "usadas aqui como aproximação para a entrada geodética do JPL.")
        st.markdown("[Fonte dos locais Apollo · NASA](https://nssdc.gsfc.nasa.gov/planetary/lunar/lunar_sites.html)")
    st.divider()
    st.subheader("Período de análise")
    day = st.date_input("Data inicial (UTC)", value=datetime.now(timezone.utc).date(),
                        min_value=datetime(1900, 1, 1).date(), max_value=datetime(2099, 12, 31).date())
    days = st.slider("Duração (dias)", 1, 14, 7)
    step = st.select_slider("Amostragem", options=[1, 3, 6, 12], value=3,
                            format_func=lambda v: f"{v} hora" if v == 1 else f"{v} horas")
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
    st.caption("As efemérides vêm do JPL. Resultados calculados pelo modelo são identificados.")
    st.markdown("[Cartografia lunar real · NASA Moon Trek](https://trek.nasa.gov/moon/)")

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

st.markdown('<div class="kicker">TELEMETRIA // EFEMÉRIDES CONSULTADAS</div>', unsafe_allow_html=True)
st.caption(f"NASA/JPL HORIZONS · {n} amostras UTC · horizonte geométrico a 0° · latitude {lat:.2f}°, longitude {lon:.2f}°")
st.caption(f"Consulta executada em UTC: {st.session_state.get('horizons_retrieved', 'não registrado')} · "
           f"período modelado: {start:%d/%m/%Y} a {stop:%d/%m/%Y}")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Sol visível · amostras", f"{sun_fraction:.0f}%", help="Fração das amostras com elevação solar > 0°. Não é porcentagem temporal contínua.")
c2.metric("Terra visível · amostras", f"{earth_fraction:.0f}%", help="Fração das amostras com elevação terrestre > 0°. Não modela montanhas nem comunicação por rádio.")
c3.metric("Energia · modelo", f"{energy:.2f} kWh", help="Energia fotovoltaica hipotética integrada a partir de irradiância por distância.")
c4.metric("Potência máxima · modelo", f"{max_power:.0f} W", help="Máxima potência calculada no intervalo amostrado.")
first = df.iloc[0]
st.caption("DISTÂNCIAS JPL // GEOMETRIA · PRIMEIRA AMOSTRA DO INTERVALO SELECIONADO")
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


v, distances, power, sky, method = st.tabs(["01 · Geometria", "02 · Distâncias JPL", "03 · Energia", "04 · Céu lunar", "05 · Métodos"])
with v:
    st.subheader("Elevação dos astros · JPL Horizons")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["instante_utc"], y=df["sun_elev"], name="Sol", mode="lines+markers",
                             line=dict(color=SOL, width=2.8), marker=dict(size=4)))
    fig.add_trace(go.Scatter(x=df["instante_utc"], y=df["earth_elev"], name="Terra", mode="lines+markers",
                             line=dict(color=TERRA, width=2.4), marker=dict(size=4)))
    fig.add_hline(y=0, line_width=1.2, line_dash="dash", line_color="#9c988f")
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

with method:
    st.subheader("Procedência e limites científicos")
    st.markdown("""
    **Fonte das posições astronômicas:** NASA/JPL Horizons, API pública, efemérides
    do tipo `OBSERVER`, origem `coord@301` (Lua), alvos `10` (Sol) e `399` (Terra),
    quantidades `4,20` (azimute/elevação e distância), `RANGE_UNITS=KM`, UTC.

    **Coordenadas:** locais personalizados com latitude geodética, longitude positiva a leste,
    altitude adotada de 0 km no elipsoide lunar. Coordenadas dos locais Apollo vêm da
    base planetocêntrica NASA/NSSDC e foram usadas como aproximação geodética;
    nenhuma correção cartográfica detalhada foi aplicada.

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
