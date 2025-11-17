

import streamlit as st
st.set_page_config(
    page_title="Sincronizador PET",
    page_icon="loguinho-azul.png",
    layout="wide"
)

from frontend import render_frontend

if __name__ == "__main__":
    render_frontend()
