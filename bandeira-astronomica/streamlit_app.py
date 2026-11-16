"""Atlas interativo independente: O Céu na Bandeira do Brasil.

Publicação própria no Streamlit Community Cloud.
Ponto de entrada: bandeira-astronomica/streamlit_app.py
"""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="O Céu na Bandeira do Brasil | Matemática & Contexto",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] {background: #07111c;}
    [data-testid="stHeader"] {background: transparent;}
    [data-testid="stMainBlockContainer"] {
        max-width: 1500px;
        padding: 0.2rem 0.5rem 1.2rem;
    }
    @media (max-width: 800px) {
      [data-testid="stMainBlockContainer"] {
        padding: 0 !important;
        max-width: 100% !important;
        width: 100% !important;
      }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

html_path = Path(__file__).resolve().parent / "index.html"
if not html_path.is_file():
    st.error("Arquivo index.html do atlas não encontrado.")
    st.stop()

# Modo de carregamento original que estava funcionando antes da troca
# para st.iframe. A navegação responsiva fica no CSS do index.html.
components.html(
    html_path.read_text(encoding="utf-8"),
    height=2300,
    scrolling=True,
)
