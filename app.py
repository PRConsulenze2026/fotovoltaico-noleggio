import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Simulatore Flusso di Cassa Fotovoltaico", layout="wide")

# CSS personalizzato per eliminare il bianco/verde e impostare il grigio scuro coordinato con il tema scuro
st.markdown("""
<style>
div.stNumberInput input, div.stTextInput input, div.stDateInput input {
    font-size: 13px !important;
    padding: 4px 8px !important;
    background-color: #2b2b2b !important;
    color: #ffffff !important;
    border: 1px solid #4f4f4f !important;
    border-radius: 4px !important;
}
input:disabled, textarea:disabled {
    background-color: #1e1e1e !important;
    -webkit-text-fill-color: #ffffff !important;
    color: #ffffff !important;
    border: 1px solid #3f3f3f !important;
    opacity: 1 !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# INIZIALIZZAZIONE SESSION STATE (CAMPI PULITI / SENZA DEFAULT FORZATI)
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
    "cessione_pct": 0.0,              # Campo ora modificabile
    "prezzo_energia_venduta": 0.0,
    "rata_mensile": 0.0,
    "manutenzione_default": 0.0,
    "riscatto_default": 0.0,
    "forma
