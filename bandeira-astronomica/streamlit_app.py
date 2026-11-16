"""Atlas interativo independente: O Céu na Bandeira do Brasil.

Publicação própria no Streamlit Community Cloud.
Ponto de entrada: bandeira-astronomica/streamlit_app.py
"""
from pathlib import Path

import streamlit as st

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
    /* No celular, o corpo do app ocupa toda a largura disponível. */
    @media (max-width: 800px) {
      [data-testid="stMainBlockContainer"] {
        padding: 0 !important;
        width: 100% !important;
        max-width: 100% !important;
      }
      [data-testid="stMainBlockContainer"] > div,
      [data-testid="stElementContainer"] {max-width:100% !important;min-width:0 !important;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

html_path = Path(__file__).resolve().parent / "index.html"
if not html_path.is_file():
    st.error("Arquivo index.html do atlas não encontrado.")
    st.stop()

# Sem a antiga altura fixa de 1600px: o frame acompanha a altura do HTML
# e evita duas áreas de rolagem no celular (requer Streamlit >= 1.56).
st.iframe(
    html_path,
    width="stretch",
    height="content",
    alt="Laboratório O céu na Bandeira do Brasil, com 27 estrelas interativas",
)
