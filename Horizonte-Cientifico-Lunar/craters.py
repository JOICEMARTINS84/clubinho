"""Análise morfológica introdutória de fotografias lunares reais.

Mede apenas propriedades da IMAGEM. Não transforma luminância em altitude.
"""
from __future__ import annotations

from io import BytesIO
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError

PHOTO_SOURCES = {
    "Fotografia 01 · mosaico de cratera (LRO/WAC)": {
        "url": "https://lroc.im-ldi.com/news/uploads/LROCiotw/4588WAC-annon.png",
        "page": "https://lroc.im-ldi.com/images/559",
        "credit": "NASA/GSFC/ASU · Lunar Reconnaissance Orbiter Camera · mosaico WAC",
        "note": "A imagem possui uma barra gráfica de 25 km. A calibração precisa ser indicada manualmente.",
    },
    "Fotografia 02 · detalhe do terreno (LRO/NAC)": {
        "url": "https://assets.science.nasa.gov/dynamicimage/assets/science/psd/photojournal/pia/pia12/pia12941/PIA12941.jpg?crop=faces%2Cfocalpoint&fit=clip&h=1000&w=1000",
        "page": "https://science.nasa.gov/photojournal/the-floor-of-tycho/",
        "credit": "NASA/GSFC/ASU · Lunar Reconnaissance Orbiter · PIA12941",
        "note": "A imagem mostra apenas um detalhe do terreno, não o contorno completo de uma cratera. Não use dimensões de outra imagem como escala desta.",
    },
}


def _decode_image(data: bytes) -> Image.Image:
    if len(data) > 16_000_000:
        raise ValueError("Arquivo muito grande (limite: 16 MB).")
    try:
        picture = Image.open(BytesIO(data))
        if picture.width * picture.height > 25_000_000:
            raise ValueError("Imagem acima de 25 milhões de pixels.")
        picture = ImageOps.exif_transpose(picture).convert("RGB")
        picture.thumbnail((1100, 1100), Image.Resampling.LANCZOS)
        return picture
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("O arquivo não é uma fotografia JPG/PNG válida.") from exc


@st.cache_data(ttl=86400, show_spinner=False)
def _load_nasa_photo(url: str) -> bytes:
    # Apenas URLs fixas da lista curada; nunca recebe endereço arbitrário do visitante.
    if url not in {source["url"] for source in PHOTO_SOURCES.values()}:
        raise ValueError("Fonte de imagem não autorizada.")
    response = requests.get(url, headers={"User-Agent": "HorizonteLunarResearch/2.1 (educational)"},
                            timeout=22)
    response.raise_for_status()
    return response.content


def sample_brightness_line(im: Image.Image, cx: int, cy: int, radius: int) -> pd.DataFrame:
    """Perfil horizontal observado, com média de 5 linhas para atenuar ruído."""
    gray = np.asarray(im.convert("L"), dtype=np.float32)
    x0 = max(0, cx-radius)
    x1 = min(gray.shape[1]-1, cx+radius)
    y0, y1 = max(0, cy-2), min(gray.shape[0], cy+3)
    values = gray[y0:y1, x0:x1+1].mean(axis=0)
    return pd.DataFrame({"deslocamento_px": np.arange(x0, x1+1)-cx,
                         "brilho_0_255": values})


def render_crater_lab():
    st.markdown("### Investigação de crateras por imagens")
    st.caption("Fotografias autênticas LRO · análise de imagem em Python · nenhuma medida topográfica é inferida do brilho")

    cphoto, cinfo = st.columns([1.2, .8], gap="medium")
    with cphoto:
        image_choice = st.selectbox(
            "Imagem para estudar",
            ["Selecione uma imagem para começar"] + list(PHOTO_SOURCES) + ["Enviar fotografia JPG/PNG"],
            key="crater_photo_choice",
            help="Escolha uma imagem real da missão LRO ou carregue uma fotografia própria."
        )
    with cinfo:
        st.markdown("**O que este módulo mede?**")
        st.caption("Tamanho em pixels, perfil de luminância e diâmetro estimado somente quando uma escala confiável é informada.")

    if image_choice == "Selecione uma imagem para começar":
        st.info("Escolha uma fotografia LRO na lista, ou envie um arquivo para iniciar a análise.")
        return

    source = PHOTO_SOURCES.get(image_choice)
    if source:
        st.caption(source["credit"])
        st.caption(source["note"])
        st.markdown(f"[Consultar imagem original e contexto científico]({source['page']})")
        try:
            with st.spinner("Carregando imagem de pesquisa..."):
                image = _decode_image(_load_nasa_photo(source["url"]))
        except (requests.RequestException, ValueError, OSError) as exc:
            st.warning(f"A fotografia externa não carregou: {str(exc)[:160]}. "
                       "Você pode baixá-la do site de origem e selecionar 'Enviar fotografia JPG/PNG'.")
            return
    else:
        st.info("Baixe uma fotografia do [NASA Moon Trek](https://trek.nasa.gov/moon/) "
                "ou do [arquivo LROC](https://data.lroc.im-ldi.com/lroc/) e carregue-a aqui.")
        image_file = st.file_uploader("Fotografia (PNG ou JPG, até 16 MB)",
                                      type=["png", "jpg", "jpeg"], key="crater_file")
        if image_file is None:
            return
        try:
            image = _decode_image(image_file.getvalue())
        except ValueError as exc:
            st.error(str(exc))
            return

    w, h = image.size
    st.caption(f"Dimensões após redimensionamento para análise: {w} × {h} pixels. "
               "As coordenadas dos controles são referentes à imagem exibida.")

    st.markdown("**01 / Marque uma estrutura circular**")
    left, right = st.columns([1.4, 1.0], gap="medium")
    with right:
        cx = st.slider("Centro horizontal · X (px)", 0, w-1, w//2, key="crater_cx")
        cy = st.slider("Centro vertical · Y (px)", 0, h-1, h//2, key="crater_cy")
        max_radius = min(cx, cy, w-1-cx, h-1-cy)
        if max_radius < 2:
            st.warning("Mova o centro para dentro da imagem para selecionar uma área.")
            return
        radius = st.slider("Raio do contorno (px)", 2, max_radius,
                           min(max_radius, max(3, min(w, h)//4)), key="crater_radius")
        st.caption("A circunferência é ajustada por você. Não é detecção automática de uma cratera.")
        st.markdown("**02 / Calibre a escala, se conhecida**")
        use_scale = st.checkbox("Tenho uma barra de escala confiável", value=False, key="crater_scale")
        km_per_px = None
        if use_scale:
            b1, b2 = st.columns(2)
            with b1:
                scale_km = st.number_input("Barra (km)", 0.001, 5000.0, 25.0,
                                            step=1.0, key="crater_scale_km")
            with b2:
                scale_px = st.number_input("Barra (pixels)", 1, max(w,h), min(120, w),
                                            step=1, key="crater_scale_px")
            km_per_px = scale_km/scale_px
            st.caption("Conte o comprimento da barra na imagem exibida, em pixels. "
                       "A projeção e a perspectiva podem causar distorções.")

    with left:
        img_fig = go.Figure(go.Image(z=np.asarray(image)))
        img_fig.add_shape(type="circle", x0=cx-radius, x1=cx+radius,
                          y0=cy-radius, y1=cy+radius,
                          line=dict(color="#f2463b", width=3), fillcolor="rgba(0,0,0,0)")
        img_fig.add_trace(go.Scatter(x=[cx], y=[cy], mode="markers",
                                     marker=dict(color="#ffdfbc", size=7, symbol="cross"),
                                     showlegend=False, hovertemplate="Centro selecionado<extra></extra>"))
        img_fig.update_layout(template="plotly_dark", paper_bgcolor="#05080e",
                              plot_bgcolor="#05080e", showlegend=False,
                              margin=dict(l=0,r=0,t=0,b=0),
                              height=min(650, max(330, int(540*h/max(w,1)))))
        img_fig.update_xaxes(range=[0,w], showgrid=False, zeroline=False,
                              showticklabels=False)
        img_fig.update_yaxes(range=[h,0], showgrid=False, zeroline=False,
                              showticklabels=False, scaleanchor="x", scaleratio=1)
        st.plotly_chart(img_fig, use_container_width=True)

    a,b,c = st.columns(3)
    diameter_px = 2*radius
    a.metric("Diâmetro marcado", f"{diameter_px} px")
    if km_per_px is not None:
        b.metric("Diâmetro estimado", f"{diameter_px*km_per_px:.2f} km")
        c.metric("Área circular estimada", f"{np.pi*(radius*km_per_px)**2:.2f} km²")
    else:
        b.metric("Escala física", "Não calibrada")
        c.metric("Área física", "Indisponível")

    st.markdown("**03 / Perfil de brilho da imagem**")
    profile = sample_brightness_line(image, cx, cy, radius)
    profile_fig = go.Figure(go.Scatter(x=profile["deslocamento_px"],
                                       y=profile["brilho_0_255"], mode="lines",
                                       line=dict(color="#74b8f6", width=2.4)))
    profile_fig.update_layout(template="plotly_dark",
                              paper_bgcolor="#05080e", plot_bgcolor="#05080e",
                              height=300, margin=dict(l=10,r=10,t=20,b=30),
                              xaxis_title="Distância horizontal ao centro (pixels)",
                              yaxis_title="Brilho observado (0–255)")
    st.plotly_chart(profile_fig, use_container_width=True)
    st.caption("Perfis escuros podem indicar sombra, composição, rugosidade ou condições de captura. "
               "Brilho NÃO é altitude e não fornece sozinho a profundidade da cratera.")

    st.download_button("Exportar perfil de brilho (CSV)",
                       profile.to_csv(index=False).encode("utf-8-sig"),
                       file_name="perfil_brilho_cratera.csv", mime="text/csv",
                       key="crater_export")
    st.markdown("**Próxima etapa científica:** associar esta região a um modelo digital de "
                "elevação (LOLA ou estéreo NAC) e comparar diâmetro, declividade e profundidade com "
                "incertezas de calibração e projeção. "
                "[Explorar perfis de elevação no NASA Moon Trek](https://trek.nasa.gov/moon/).")
