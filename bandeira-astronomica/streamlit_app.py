"""Atlas interativo independente: O Céu na Bandeira do Brasil.

Publicação própria no Streamlit Community Cloud.
Ponto de entrada: bandeira-astronomica/streamlit_app.py

O atlas é uma página HTML autossuficiente (index.html), montada por build.py a
partir de src/ e dos JSON de dados. Este arquivo só a exibe dentro do Streamlit.
"""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

APP_DIR = Path(__file__).resolve().parent
HTML_PATH = APP_DIR / "index.html"

# Altura inicial do iframe. A própria página a ajusta ao conteúdo assim que carrega
# (veja fitFrameHeight em src/app.js); este valor só vale se o ajuste não puder rodar.
FALLBACK_HEIGHT = 2400

# Estilos do contêiner externo. O documento no iframe usa src/style.css.
PAGE_CSS = """
<style>
  /* Estrutura nativa do Streamlit: sem menus ou rodapé decorativo. */
  #MainMenu, footer, [data-testid="stHeader"],
  [data-testid="stToolbar"], [data-testid="stDecoration"],
  [data-testid="stStatusWidget"], [data-testid="stAppDeployButton"] {
    display: none !important;
  }
  [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background: #f7f7f5;
  }
  /* Retira o recuo reservado ao cabeçalho e evita cortar o atlas. */
  [data-testid="stMainBlockContainer"], .block-container {
    max-width: 1680px !important;
    width: 100% !important;
    padding: 0 !important;
  }
  [data-testid="stVerticalBlock"] { gap: 0; }
  iframe[title="streamlit.components.v1.html"] {
    display: block;
    border: 0;
    width: 100%;
  }
</style>
"""

st.set_page_config(
    page_title="O Céu na Bandeira do Brasil | Matemática & Contexto",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(PAGE_CSS, unsafe_allow_html=True)

if not HTML_PATH.is_file():
    st.error("Arquivo index.html do atlas não encontrado. Rode `python build.py`.")
    st.stop()

# components.html é o modo de carregamento que já funcionava em produção
# (a troca por st.iframe havia causado problemas de inicialização).
components.html(
    HTML_PATH.read_text(encoding="utf-8"),
    height=FALLBACK_HEIGHT,
    scrolling=True,
)
