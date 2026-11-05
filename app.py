import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Simulatore FV Noleggio",
    layout="wide"
)

# ---------------------------------------------------------
# STILE CSS PERSONALIZZATO
# ---------------------------------------------------------
css_code = """
<style>
div.stNumberInput input,
div.stTextInput input,
div.stDateInput input {
    font-size: 13px !important;
    padding: 4px 8px !important;
    background-color: #2b2b2b !important;
    color: #ffffff !important;
    border: 1px solid #4f4f4f !important;
    border-radius: 4px !important;
}
input:disabled,
textarea:disabled {
    background-color: #1e1e1e !important;
    -webkit-text-fill-color: #ffffff !important;
    color: #ffffff !important;
    border: 1px solid #3f3f3f !important;
    opacity: 1 !important;
}
div[data-testid="stDataFrame"] th {
    white-space: normal !important;
    word-break: break-word !important;
    height: 65px !important;
    min-height: 65px !important;
    vertical-align: middle !important;
}
div[data-testid="stDataFrame"] th div {
    white-space: normal !important;
    word-break: break-word !important;
    overflow: visible !important;
}
div[data-testid="stDataFrame"] > div {
    max-height: none !important;
}
</style>
"""
st.markdown(css_code, unsafe_allow_html=True)

# ---------------------------------------------------------
# INIZIALIZZAZIONE SESSION STATE
# ---------------------------------------------------------
DEFAULTS = {
    "potenza_kwp": 0.0,
    "azienda": "",
    "indirizzo": "",
    "citta": "",
    "cap": "",
    "prov": "",
    "protocollo": "",
    "data_offerta": pd.to_datetime("today").date(),
    "prod_impianto": 0.0,
    "durata_noleggio": 7,
    "autoconsumo_pct": 0.0,
    "costo_energia_pagata": 0.0,
    "cessione_pct": 0.0,
    "prezzo_energia_venduta": 0.00000,
    "rata_mensile": 0.0,
    "manutenzione_default": 0.0,
    "riscatto_default": 0.0,
    "forma_giuridica": "Società di Capitali (S.r.l., S.p.A.)",
    "regione": "Puglia",
    "add_comunale": 0.8,
}

for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val

def reset_dati():
    for key, val in DEFAULTS.items():
        st.session_state[key] = val
    st.rerun()

# ---------------------------------------------------------
# INTESTAZIONE & RESET
# ---------------------------------------------------------
col_title, col_reset = st.columns([4, 1])
with col_title:
    title_text = (
        "⚡ Simulatore Flusso di Cassa "
        "Fotovoltaico in Noleggio Operativo"
    )
    st.title(title_text)

with col_reset:
    st.write("")
    if st.button("🔄 Reset Dati", use_container_width=True, type="primary"):
        reset_dati()

st.markdown("---")

# ---------------------------------------------------------
# 0. ANAGRAFICA & DATI OFFERTA
# ---------------------------------------------------------
st.header("📄 Anagrafica e Dati Offerta")

col_d_top1, col_d_top2 = st.columns([4, 1])
with col_d_top2:
    st.date_input("DATA", key="data_offerta")

col_a1, col_a2, col_a3 = st.columns([3, 1, 1])
with col_a1:
    off_label = (
        "**OFFERTA PRELIMIN
