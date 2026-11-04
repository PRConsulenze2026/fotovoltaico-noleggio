import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Simulatore Flusso di Cassa Fotovoltaico", layout="wide")

# CSS per personalizzare i campi di input (verde chiaro) e normalizzare i font
st.markdown("""
<style>
div.stNumberInput input {
    font-size: 13px !important;
    padding: 2px 6px !important;
    background-color: #e2efda !important;
}
div.stTextInput input {
    font-size: 13px !important;
    padding: 2px 6px !important;
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
    "prod_impianto": 14000.0,         # B2
    "durata_noleggio": 7,             # C2
    "autoconsumo_pct": 80.0,          # C4
    "costo_energia_pagata": 0.25,     # C6
    "prezzo_energia_venduta": 0.10,   # C10
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
# 2. BENEFICI ENERGETICI (LAYOUT ESATTO A 3/4 COLONNE DA EXCEL)
# ---------------------------------------------------------
st.header("💡 Benefici Energetici")

prod_impianto = st.session_state["prod_impianto"]
durata_noleggio = st.session_state["durata_noleggio"]
autoconsumo_pct = st.session_state["autoconsumo_pct"] / 100.0
costo_energia = st.session_state["costo_energia_pagata"]
prezzo_vendita = st.session_state["prezzo_energia_venduta"]
cessione_pct = 1.0 - autoconsumo_pct

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
    st.number_input("C6", step=0.01, key="costo_energia_pagata", label_visibility="collapsed")
with col_3d:
    st.markdown("*€.*")
    st.text_input("D5", value=f"€ {costo_energia:.5f}", disabled=True, label_visibility="collapsed")

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
    st.text_input("C8", value=f"{cessione_pct*100:.2f}%", disabled=True, label_visibility="collapsed")
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
    st.number_input("C10", step=0.01, key="prezzo_energia_venduta", label_visibility="collapsed")
with col_5d:
    st.markdown("*€.*")
    st.text_input("D9", value=f"€ {prezzo_vendita:.2f}", disabled=True, label_visibility="collapsed")

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
# 3. PARAMETRI NOLEGGIO OPERATIVO
# ---------------------------------------------------------
st.header("💳 Parametri Noleggio Operativo")
col_n1, col_n2 = st.columns(2)
with col_n1:
    st.number_input("A2: Rata Mensile Noleggio (€)", step=10.0, key="rata_mensile")
with col_n2:
    rata_bimestrale = st.session_state["rata_mensile"] * 2.0
    noleggio_annuale = rata_bimestrale * 6.0
    st.write(f"**A4 Rata Bimestrale:** € {rata_bimestrale:.2f}")
    st.write(f"**Noleggio Annuale (D2):** € {noleggio_annuale:.2f}")

# ---------------------------------------------------------
# 4. PERDITA DI ENERGIA E FLUSSI A 25 ANNI
# ---------------------------------------------------------
anni = list(range(1, 26))
perdita_cumulata = [0.0] + [0.005 * (a - 1) for a in anni[1:]]

perdita_auto_kwh = [- (energia_autoconsumata * p) if i > 0 else 0 for i, p in enumerate(perdita_cumulata)]
auto_kwh_netto = [energia_autoconsumata + p for p in perdita_auto_kwh]

perdita_vendita_kwh = [- (energia_venduta * p) if i > 0 else 0 for i, p in enumerate(perdita_cumulata)]
vendita_kwh_netto = [energia_venduta + p for p in perdita_vendita_kwh]

risparmio_autoconsumo_eur = [kwh * costo_energia for kwh in auto_kwh_netto]
ricavo_vendita_eur = [kwh * prezzo_vendita for kwh in vendita_kwh_netto]
totale_benefici_energetici_25 = [r + v for r, v in zip(risparmio_autoconsumo_eur, ricavo_vendita_eur)]

def calcola_coefficiente_fiscale(forma, reg, add_com):
    if forma == "Regime Forfettario":
        return 0.0
    info_reg = regioni_db[reg]
    irap = info_reg["irap"]
    if forma == "Società di Capitali (S.r.l., S.p.A.)":
        return 0.24 + irap
    else:
        return 0.35 + irap + info_reg["add_reg_min"] + add_com

coeff_fiscale = calcola_coefficiente_fiscale(st.session_state["forma_giuridica"], st.session_state["regione"], st.session_state["add_comunale"] / 100.0)

beneficio_fiscale_mensile = st.session_state["rata_mensile"] * coeff_fiscale
beneficio_fiscale_annuale = np.ceil(beneficio_fiscale_mensile) * 12.0

st.markdown("---")
st.subheader("📊 Flussi di Cassa Complessivi (25 Anni)")

col_opt1, col_opt2 = st.columns(2)
with col_opt1:
    st.number_input("Manutenzione Annuale (€)", step=50.0, key="manutenzione_default")
with col_opt2:
    st.number_input("Riscatto Finale (Anno 7) (€)", step=50.0, key="riscatto_default")

manut_val = st.session_state["manutenzione_default"]
riscatto_val = st.session_state["riscatto_default"]

df_flussi = pd.DataFrame({
    "Anno": anni,
    "Benefici Energetici (€)": totale_benefici_energetici_25,
    "Benefici Fiscali (€)": [beneficio_fiscale_annuale if a <= durata_noleggio else np.nan for a in anni],
    "Noleggio (€)": [-noleggio_annuale if a <= durata_noleggio else np.nan for a in anni],
    "Manutenzione Annuale (€)": [manut_val] * 25,
    "Riscatto (€)": [riscatto_val if a == durata_noleggio else np.nan for a in anni]
})

df_flussi["Flusso Netto (€)"] = df_flussi[["Benefici Energetici (€)", "Benefici Fiscali (€)", "Noleggio (€)", "Manutenzione Annuale (€)", "Riscatto (€)"]].sum(axis=1)
df_flussi["Cumulato (€)"] = df_flussi["Flusso Netto (€)"].cumsum()

st.dataframe(df_flussi.style.format({
    "Benefici Energetici (€)": "€ {:.2f}",
    "Benefici Fiscali (€)": lambda x: f"€ {x:.2f}" if pd.notnull(x) else "",
    "Noleggio (€)": lambda x: f"€ {x:.2f}" if pd.notnull(x) else "",
    "Manutenzione Annuale (€)": "€ {:.2f}",
    "Riscatto (€)": lambda x: f"€ {x:.2f}" if pd.notnull(x) else "",
    "Flusso Netto (€)": "€ {:.2f}",
    "Cumulato (€)": "€ {:.2f}"
}), use_container_width=True)

# Totali Generali
st.markdown("### 📈 Totali Generali")
tot_energetici = sum(totale_benefici_energetici_25)
tot_fiscali = beneficio_fiscale_annuale * durata_noleggio
tot_noleggio = -noleggio_annuale * durata_noleggio
tot_manutenzione = manut_val * 25
tot_riscatto = riscatto_val
tot_netto = tot_energetici + tot_fiscali + tot_noleggio + tot_manutenzione + tot_riscatto

m1, m2, m3, m4 = st.columns(4)
m1.metric("Totale Benefici Energetici", f"€ {tot_energetici:,.2f}")
m2.metric("Totale Benefici Fiscali", f"€ {tot_fiscali:,.2f}")
m3.metric("Totale Noleggio Operativo", f"€ {tot_noleggio:,.2f}")
m4.metric("Flusso Netto Cumulato a 25 Anni", f"€ {tot_netto:,.2f}")
