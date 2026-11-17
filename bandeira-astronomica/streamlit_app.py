"""Atlas interativo independente: O Céu na Bandeira do Brasil.

Publicação própria no Streamlit Community Cloud.
Versão publicada: mesa de consulta astronômica, com índice de estrelas,
prancha interativa da bandeira e ficha técnica das constelações.
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

PAGE_CSS = """
<style>
  [data-testid="stAppViewContainer"] { background: #f6f4ee; }
  [data-testid="stHeader"] { background: #f6f4ee; }
  [data-testid="stMainBlockContainer"] {
    max-width: 1500px;
    padding: 0 !important;
  }
  @media (max-width: 800px) {
    [data-testid="stMainBlockContainer"] {
      padding: 0 !important;
      max-width: 100% !important;
      width: 100% !important;
    }
  }
</style>
"""

st.set_page_config(
    page_title="O Céu na Bandeira do Brasil | Matemática & Contexto",
    page_icon="🇧🇷",
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
