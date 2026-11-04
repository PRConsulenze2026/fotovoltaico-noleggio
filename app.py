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
    "cessione_pct": 0.0,
    "prezzo_energia_venduta": 0.0,
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
# INTESTAZIONE & TASTO DI RESET GENERALE
# ---------------------------------------------------------
col_title, col_reset = st.columns([4, 1])
with col_title:
    st.title("⚡ Simulatore Flusso di Cassa Fotovoltaico in Noleggio Operativo")
with col_reset:
    st.write("")
    if st.button("🔄 Reset Tutti i Dati", use_container_width=True, type="primary"):
        reset_dati()

st.markdown("---")

# ---------------------------------------------------------
# 0. FOGLIO ANAGRAFICA & DATI OFFERTA
# ---------------------------------------------------------
st.header("📄 Anagrafica e Dati Offerta")

col_d_top1, col_d_top2 = st.columns([4, 1])
with col_d_top2:
    st.date_input("DATA", key="data_offerta")

col_a1, col_a2, col_a3 = st.columns([3, 1, 1])
with col_a1:
    st.markdown("**OFFERTA PRELIMINARE PER IL NOLEGGIO DI UN IMPIANTO FOTOVOLTAICO DA:**")
with col_a2:
    st.number_input("kWp", step=0.001, format="%.3f", label_visibility="collapsed", key="potenza_kwp")
with col_a3:
    st.markdown("**kWp**")

col_b1, col_b2 = st.columns([3, 2])
with col_b1:
    st.markdown("**PER AUTOCONSUMO DI ENERGIA**")
with col_b2:
    st.text_input("Protocollo", placeholder="Protocollo...", label_visibility="collapsed", key="protocollo")

st.markdown("---")

col_c1, col_c2 = st.columns(2)
with col_c1:
    st.text_input("AZIENDA (Nome Cliente / Ragione Sociale)", placeholder="Inserisci nome azienda...", key="azienda")
    st.text_input("INDIRIZZO", placeholder="Via / Piazza e civico...", key="indirizzo")
with col_c2:
    st.text_input("CITTA'", placeholder="Città...", key="citta")
    col_cp1, col_cp2 = st.columns([2, 1])
    with col_cp1:
        st.text_input("CAP", placeholder="CAP", key="cap")
    with col_cp2:
        st.text_input("PROV.", placeholder="Prov.", key="prov")

st.markdown("---")

# ---------------------------------------------------------
# 1. INQUADRAMENTO FISCALE (DEFAULT INTERNO)
# ---------------------------------------------------------
regioni_db = {
    "Abruzzo": {"irap": 0.0390, "add_reg_min": 0.0173, "add_reg_max": 0.0333},
    "Basilicata": {"irap": 0.0390, "add_reg_min": 0.0123, "add_reg_max": 0.0233},
    "Calabria": {"irap": 0.0482, "add_reg_min": 0.0203, "add_reg_max": 0.0333},
    "Campania": {"irap": 0.0497, "add_reg_min": 0.0203, "add_reg_max": 0.0333},
    "Emilia-Romagna": {"irap": 0.0390, "add_reg_min": 0.0133, "add_reg_max": 0.0227},
    "Friuli-Venezia Giulia": {"irap": 0.0390, "add_reg_min": 0.0123, "add_reg_max": 0.0123},
    "Lazio": {"irap": 0.0482, "add_reg_min": 0.0173, "add_reg_max": 0.0333},
    "Liguria": {"irap": 0.0390, "add_reg_min": 0.0123, "add_reg_max": 0.0333},
    "Lombardia": {"irap": 0.0390, "add_reg_min": 0.0123, "add_reg_max": 0.0173},
    "Marche": {"irap": 0.0390, "add_reg_min": 0.0123, "add_reg_max": 0.0173},
    "Molise": {"irap": 0.0482, "add_reg_min": 0.0173, "add_reg_max": 0.0333},
    "Piemonte": {"irap": 0.0390, "add_reg_min": 0.0162, "add_reg_max": 0.0333},
    "Puglia": {"irap": 0.0482, "add_reg_min": 0.0123, "add_reg_max": 0.0173},
    "Sardegna": {"irap": 0.0293, "add_reg_min": 0.0123, "add_reg_max": 0.0123},
    "Sicilia": {"irap": 0.0390, "add_reg_min": 0.0123, "add_reg_max": 0.0173},
    "Toscana": {"irap": 0.0390, "add_reg_min": 0.0142, "add_reg_max": 0.0173},
    "Trentino-Alto Adige": {"irap": 0.0346, "add_reg_min": 0.0123, "add_reg_max": 0.0123},
    "Umbria": {"irap": 0.0390, "add_reg_min": 0.0123, "add_reg_max": 0.0183},
    "Valle d'Aosta": {"irap": 0.0390, "add_reg_min": 0.0123, "add_reg_max": 0.0123},
    "Veneto": {"irap": 0.0390, "add_reg_min": 0.0123, "add_reg_max": 0.0123},
}

# ---------------------------------------------------------
# 2. BENEFICI ENERGETICI (LAYOUT ESATTO A 4 COLONNE DA EXCEL)
# ---------------------------------------------------------
st.header("💡 Benefici Energetici")

prod_impianto = st.session_state["prod_impianto"]
durata_noleggio = st.session_state["durata_noleggio"] if st.session_state["durata_noleggio"] > 0 else 1
autoconsumo_pct = st.session_state["autoconsumo_pct"] / 100.0
costo_energia = st.session_state["costo_energia_pagata"]
prezzo_vendita = st.session_state["prezzo_energia_venduta"]
cessione_pct = st.session_state["cessione_pct"] / 100.0

prod_media_annuale = prod_impianto / durata_noleggio if durata_noleggio > 0 else 0
energia_autoconsumata = prod_media_annuale * autoconsumo_pct
risparmio_autoconsumo = energia_autoconsumata * costo_energia
energia_venduta = prod_media_annuale * cessione_pct
ricavo_vendita = energia_venduta * prezzo_vendita
totale_benefici = risparmio_autoconsumo + ricavo_vendita

# --- Blocco 1 ---
col_1a, col_1b, col_1c, col_1d = st.columns([3,
