import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Simulatore Flusso di Cassa Fotovoltaico", layout="wide")

# CSS personalizzato per:
# 1. Colore grigio scuro e testo bianco nei campi
# 2. Altezza maggiorata e word wrapping automatico delle intestazioni (th) delle tabelle
# 3. Rimozione delle barre di scorrimento interne alle tabelle
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
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# INIZIALIZZAZIONE SESSION STATE (CAMPI PULITI)
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
    "Veneto": {"irap": 0.0390, "add_reg_min": 0.0123, "add_reg_max": 0.0123}
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
col_1a, col_1b, col_1c, col_1d = st.columns([3, 2, 2, 2])
with col_1a:
    st.markdown("**Produzione Media Annuale**")
with col_1b:
    st.markdown("*Produzione Impianto/kWh*")
    st.number_input("B2", step=500.0, key="prod_impianto", label_visibility="collapsed")
with col_1c:
    st.markdown("*Anni Durata Noleggio*")
    st.number_input("C2", step=1, key="durata_noleggio", label_visibility="collapsed")
with col_1d:
    st.markdown("*kWh*")
    st.text_input("D1", value=f"{prod_media_annuale:,.2f}", disabled=True, label_visibility="collapsed")

st.markdown("---")

# --- Blocco 2 ---
col_2a, col_2b, col_2c, col_2d = st.columns([3, 2, 2, 2])
with col_2a:
    st.markdown("**Energia Autoconsumata**")
with col_2b:
    st.markdown("*Produzione Media Annuale*")
    st.text_input("D2", value=f"{prod_media_annuale:,.2f}", disabled=True, label_visibility="collapsed")
with col_2c:
    st.markdown("*Autoconsumo/Produzione in %*")
    st.number_input("C4", step=5.0, key="autoconsumo_pct", label_visibility="collapsed")
with col_2d:
    st.markdown("*kWh*")
    st.text_input("D3", value=f"{energia_autoconsumata:,.2f}", disabled=True, label_visibility="collapsed")

st.markdown("---")

# --- Blocco 3 ---
col_3a, col_3b, col_3c, col_3d = st.columns([3, 2, 2, 2])
with col_3a:
    st.markdown("**Risparmio in Autoconsumo**")
with col_3b:
    st.markdown("*Energia Autoconsumata*")
    st.text_input("D4", value=f"{energia_autoconsumata:,.2f}", disabled=True, label_visibility="collapsed")
with col_3c:
    st.markdown("*Costo Energia Attualmente Pagata in kWh*")
    st.number_input("C6", step=0.00001, format="%.5f", key="costo_energia_pagata", label_visibility="collapsed")
with col_3d:
    st.markdown("*€.*")
    st.text_input("D5", value=f"€ {risparmio_autoconsumo:,.2f}", disabled=True, label_visibility="collapsed")

st.markdown("---")

# --- Blocco 4 ---
col_4a, col_4b, col_4c, col_4d = st.columns([3, 2, 2, 2])
with col_4a:
    st.markdown("**Energia Venduta**")
with col_4b:
    st.markdown("*Produzione Media Annuale*")
    st.text_input("D6", value=f"{prod_media_annuale:,.2f}", disabled=True, label_visibility="collapsed")
with col_4c:
    st.markdown("*Cessione EE/Produzione di Energia in %*")
    st.number_input("C8", step=1.0, format="%.2f", key="cessione_pct", label_visibility="collapsed")
with col_4d:
    st.markdown("*kWh*")
    st.text_input("D7", value=f"{energia_venduta:,.2f}", disabled=True, label_visibility="collapsed")

st.markdown("---")

# --- Blocco 5 ---
col_5a, col_5b, col_5c, col_5d = st.columns([3, 2, 2, 2])
with col_5a:
    st.markdown("**Ricavo dalla Vendita**")
with col_5b:
    st.markdown("*Energia Venduta*")
    st.text_input("D8", value=f"{energia_venduta:,.2f}", disabled=True, label_visibility="collapsed")
with col_5c:
    st.markdown("*Prezzo Energia Venduta in kWh*")
    st.number_input("C10", step=0.00001, format="%.5f", key="prezzo_energia_venduta", label_visibility="collapsed")
with col_5d:
    st.markdown("*€.*")
    st.text_input("D9", value=f"€ {ricavo_vendita:,.2f}", disabled=True, label_visibility="collapsed")

st.markdown("---")

# --- Blocco 6 ---
col_6a, col_6b, col_6c, col_6d = st.columns([3, 2, 2, 2])
with col_6a:
    st.markdown("**Totale Benefici Energetici per Anno**")
with col_6b:
    st.markdown("*Risparmio in Autoconsumo*")
    st.text_input("D10", value=f"€ {risparmio_autoconsumo:,.2f}", disabled=True, label_visibility="collapsed")
with col_6c:
    st.markdown("*Ricavo dalla Vendita*")
    st.text_input("D11", value=f"€ {ricavo_vendita:,.2f}", disabled=True, label_visibility="collapsed")
with col_6d:
    st.markdown("*€. (Totale)*")
    st.text_input("D12", value=f"€ {totale_benefici:,.2f}", disabled=True, label_visibility="collapsed")

st.markdown("---")

# ---------------------------------------------------------
# 3. PERDITE DI ENERGIA (nei 25 ANNI - MULTIINDEX ESATTO DA EXCEL)
# ---------------------------------------------------------
st.header("📉 Perdite di Energia (nei 25 Anni)")

anni = list(range(1, 26))
efficienza_residua = [1.0 if a == 1 else round(1.0 - 0.005 * (a - 1), 3) for a in anni]
perdita_cumulata = [0.0 if a == 1 else round(0.005 * (a - 1), 3) for a in anni]

perdita_auto_kwh = [0.0 if a == 1 else - (energia_autoconsumata * perdita_cumulata[i]) for i, a in enumerate(anni)]
auto_kwh_netto = [energia_autoconsumata + perdita_auto_kwh[i] for i in range(25)]

perdita_vendita_kwh = [0.0 if a == 1 else - (energia_venduta * perdita_cumulata[i]) for i, a in enumerate(anni)]
vendita_kwh_netto = [energia_venduta + perdita_vendita_kwh[i] for i in range(25)]

risparmio_auto_eur = [auto_kwh_netto[i] * costo_energia for i in range(25)]
ricavo_vendita_eur = [vendita_kwh_netto[i] * prezzo_vendita for i in range(25)]
totale_benefici_perdita = [risparmio_auto_eur[i] + ricavo_vendita_eur[i] for i in range(25)]

# Definizione delle colonne MultiIndex esattamente identiche al foglio Excel
multi_columns = pd.MultiIndex.from_tuples([
    ("Anno", ""),
    ("Efficienza Residua Stimata (%)", ""),
    ("Perdita di Energia Cumulata (%)", ""),
    ("Energia Autoconsumata", "Perdita in kWh"),
    ("Energia Autoconsumata", "kWh"),
    ("Energia Venduta", "Perdita in kWh"),
    ("Energia Venduta", "kWh"),
    ("Risparmio in Autoconsumo", "€"),
    ("Ricavo dalla Vendita", "€"),
    ("Totale Benefici Energetici per Anno", "€")
])

df_perdita_data = list(zip(
    anni,
    efficienza_residua,
    perdita_cumulata,
    perdita_auto_kwh,
    auto_kwh_netto,
    perdita_vendita_kwh,
    vendita_kwh_netto,
    risparmio_auto_eur,
    ricavo_vendita_eur,
    totale_benefici_perdita
))

df_perdita = pd.DataFrame(df_perdita_data, columns=multi_columns)

st.dataframe(df_perdita.style.format({
    ("Efficienza Residua Stimata (%)", ""): "{:.2%}",
    ("Perdita di Energia Cumulata (%)", ""): "{:.2%}",
    ("Energia Autoconsumata", "Perdita in kWh"): "{:,.2f}",
    ("Energia Autoconsumata", "kWh"): "{:,.2f}",
    ("Energia Venduta", "Perdita in kWh"): "{:,.2f}",
    ("Energia Venduta", "kWh"): "{:,.2f}",
    ("Risparmio in Autoconsumo", "€"): "€ {:.2f}",
    ("Ricavo dalla Vendita", "€"): "€ {:.2f}",
    ("Totale Benefici Energetici per Anno", "€"): "€ {:.2f}"
}), use_container_width=True, hide_index
