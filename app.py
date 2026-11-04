import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Simulatore Flusso di Cassa Fotovoltaico", layout="wide")

# CSS personalizzato per evidenziare i campi di input modificabili (verde chiaro) e normalizzare la dimensione dei font
st.markdown("""
<style>
div.stNumberInput input {
    font-size: 14px !important;
    padding: 4px 8px !important;
}
div.stTextInput input {
    font-size: 14px !important;
    padding: 4px 8px !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# VALORI DI DEFAULT ED INIZIALIZZAZIONE SESSION STATE
# ---------------------------------------------------------
DEFAULTS = {
    "potenza_kwp": 30.380,
    "azienda": "",
    "indirizzo": "",
    "citta": "",
    "cap": "",
    "prov": "",
    "protocollo": "",
    "data_offerta": pd.to_datetime("today").date(),
    "prod_impianto": 14000.0,         # B2 (Verde)
    "durata_noleggio": 7,             # C2
    "autoconsumo_pct": 80.0,          # C4 (Verde)
    "costo_energia_pagata": 0.25,     # C6 (Verde)
    "prezzo_energia_venduta": 0.10,   # C10 (Verde)
    "rata_mensile": 250.0,
    "manutenzione_default": -530.0,
    "riscatto_default": -500.0,
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

# DATA posizionata in alto sopra il numero kWp
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
    # CAP e PROV ridotti e affiancati sotto CITTA'
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
# 2. BENEFICI ENERGETICI (TABELLA A 4 COLONNE ALLINEATA AL FOGLIO EXCEL)
# ---------------------------------------------------------
st.header("💡 Benefici Energetici")
st.markdown("*(I campi con sfondo verde chiaro sono modificabili, gli altri derivano dalle formule del foglio Excel)*")

prod_impianto = st.session_state["prod_impianto"]         # B2 (Verde)
durata_noleggio = st.session_state["durata_noleggio"]     # C2
autoconsumo_pct = st.session_state["autoconsumo_pct"] / 100.0  # C4 (Verde)
costo_energia = st.session_state["costo_energia_pagata"]  # C6 (Verde)
prezzo_vendita = st.session_state["prezzo_energia_venduta"] # C10 (Verde)
cessione_pct = 1.0 - autoconsumo_pct                    # C8

prod_media_annuale = prod_impianto / durata_noleggio if durata_noleggio > 0 else 0  # D2
energia_autoconsumata = prod_media_annuale * autoconsumo_pct                         # D4
risparmio_autoconsumo = energia_autoconsumata * costo_energia                        # D6
energia_venduta = prod_media_annuale * cessione_pct                                  # D8
ricavo_vendita = energia_venduta * prezzo_vendita                                    # D10
totale_benefici = risparmio_autoconsumo + ricavo_vendita                             # D12

# Struttura Tabellare a 4 Colonne allineata riga per riga
col_h1, col_h2, col_h3, col_h4 = st.columns([2.5, 2, 2.5, 1.5])

with col_h1:
    st.markdown("---")
    st.markdown("**Produzione Media Annuale**")
    st.markdown("---")
    st.markdown("**Energia Autoconsumata**")
    st.markdown("---")
    st.markdown("**Risparmio in Autoconsumo**")
    st.markdown("---")
    st.markdown("**Energia Venduta**")
    st.markdown("---")
    st.markdown("**Ricavo dalla Vendita**")
    st.markdown("---")
    st.markdown("**Totale Benefici Energetici per Anno**")

with col_h2:
    st.markdown("*Produzione Impianto/kWh*")
    st.number_input("B2", step=500.0, key="prod_impianto", label_visibility="collapsed")
    st.markdown("*Produzione Media Annuale*")
    st.text_input("D2", value=f"{energia_autoconsumata:,.2f}", disabled=True, label_visibility="collapsed")
    st.markdown("*Energia Autoconsumata*")
    st.text_input("D4", value=f"€ {risparmio_autoconsumo:,.2f}", disabled=True, label_visibility="collapsed")
    st.markdown("*Produzione Media Annuale*")
    st.text_input("D8_1", value=f"{energia_venduta:,.2f}", disabled=True, label_visibility="collapsed")
    st.markdown("*Energia Venduta*")
    st.text_input("D10_1", value=f"€ {ricavo_vendita:,.2f}", disabled=True, label_visibility="collapsed")
    st.markdown("*Risparmio in Autoconsumo*")
    st.text_input("D12_1", value=f"€ {totale_benefici:,.2f}", disabled=True, label_visibility="collapsed")

with col_h3:
    st.markdown("*Anni Durata Noleggio*")
    st.number_input("C2", step=1, key="durata_noleggio", label_visibility="collapsed")
    st.markdown("*Autoconsumo
