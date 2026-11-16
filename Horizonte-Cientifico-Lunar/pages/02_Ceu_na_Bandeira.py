"""Página do atlas astronômico da bandeira brasileira.
Integrada ao aplicativo Horizonte Científico Lunar no Streamlit Community Cloud.
A apresentação HTML/CSS/JavaScript permanece isolada em iframe para evitar
interferência com os painéis e estilos do laboratório lunar.
"""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="O Céu na Bandeira do Brasil | Matemática & Contexto",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] {background: #07111c;}
[data-testid="stMainBlockContainer"] {
  padding: 0.6rem 0.25rem 1.2rem;
  max-width: 1600px;
}
iframe[title="streamlit_components.v1.html"] {
  border: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# O Streamlit executa a partir da raiz do repositório; usamos caminho absoluto
# relativo à localização deste script para funcionar em nuvem e localmente.
page_html = Path(__file__).resolve().parents[2] / "bandeira-astronomica" / "index.html"
if not page_html.is_file():
    st.error("Não foi possível localizar o atlas da bandeira no repositório.")
    st.stop()

components.html(page_html.read_text(encoding="utf-8"), height=1500, scrolling=True)
st.caption("Matemática & Contexto · Projeto educativo de Joice Souza Martins Santos.")
