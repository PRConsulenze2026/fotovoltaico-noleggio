import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Simulatore Flusso di Cassa Fotovoltaico", layout="wide")

# ---------------------------------------------------------
# VALORI DI DEFAULT ED INIZIALIZZAZIONE SESSION STATE
# ---------------------------------------------------------
DEFAULTS = {
    "potenza_kwp": 30.0,
    "azienda": "",
    "indirizzo": "",
    "citta": "",
    "cap": "",
    "prov": "",
    "autoconsumo_nota": "",
    "prod_impianto": 14000.0,         # B2 (Produzione Impianto kWh)
    "durata_noleggio": 7,             # C2 (Anni Durata Noleggio)
    "autoconsumo_pct": 80.0,          # C4 (Autoconsumo %)
    "costo_energia_pagata": 0.25,     # C6 (Costo Energia €/kWh)
    "prezzo_energia_venduta": 0.10,   # C10 (Prezzo Energia Venduta €/kWh)
    "rata_mensile": 250.0,
    "manutenzione_default": -530.0,
    "riscatto_default": -500.0,
    "add_comunale": 0.8,
}

for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val

def reset_dati():
    for key, val in DEFAULTS.items():
        st.session_state[key] = val

# ---------------------------------------------------------
# INTESTAZIONE
# ---------------------------------------------------------
st.title("⚡ Simulatore Flusso di Cassa Fotovoltaico in Noleggio Operativo")

# ---------------------------------------------------------
# 0. FOGLIO ANAGRAFICA & DATI OFFERTA
# ---------------------------------------------------------
st.header("📄 Anagrafica e Dati Offerta")

col_a1, col_a2, col_a3 = st.columns([3, 1, 1])
with col_a1:
    st.markdown("**OFFERTA PRELIMINARE PER IL NOLEGGIO DI UN IMPIANTO FOTOVOLTAICO DA:**")
with col_a2:
    st.number_input("kWp", step=1.0, label_visibility="collapsed", key="potenza_kwp")
with col_a3:
    st.markdown("**kWp**")

col_b1, col_b2 = st.columns([3, 2])
with col_b1:
    st.markdown("**PER AUTOCONSUMO DI ENERGIA** *(Campo descrittivo fisso)*")
with col_b2:
    st.text_input("Note Autoconsumo", placeholder="Inserisci eventuale nota...", label_visibility="collapsed", key="autoconsumo_nota")

st.markdown("---")

col_c1, col_c2 = st.columns(2)
with col_c1:
    st.text_input("AZIENDA (Nome Cliente / Ragione Sociale)", placeholder="Inserisci nome azienda...", key="azienda")
    st.text_input("INDIRIZZO", placeholder="Via / Piazza e civico...", key="indirizzo")
with col_c2:
    st.text_input("CITTA'", placeholder="Città...", key="citta")
    
col_d1, col_d2, col_d3 = st.columns([2, 1, 1])
with col_d1:
    st.text_input("CAP", placeholder="CAP", key="cap")
with col_d2:
    st.text_input("PROV.", placeholder="Provincia (es. FG)", key="prov")
with col_d3:
    st.date_input("DATA", value=pd.to_datetime("today"))

st.markdown("---")

# ---------------------------------------------------------
# 1. ANAGRAFICA FISCALE E REGIONALE
# ---------------------------------------------------------
st.sidebar.header("⚙️ Opzioni & Inquadramento")
st.sidebar.button("🔄 Reset Dati ai Valori Iniziali", on_click=reset_dati, use_container_width=True)
st.sidebar.markdown("---")

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

forma_giuridica = st.sidebar.selectbox(
    "Forma Giuridica / Regime Fiscale",
    [
        "Società di Capitali (S.r.l., S.p.A.)",
        "Ditta Individuale / S.n.c. (Scaglione IRPEF medio)",
        "Ditta Individuale / S.n.c. (Scaglione IRPEF massimo)",
        "Regime Forfettario"
    ]
)

regione = st.sidebar.selectbox("Regione di Appartenenza", list(regioni_db.keys()))
add_comunale_val = st.sidebar.number_input("Addizionale Comunale (%)", step=0.1, key="add_comunale") / 100.0

def calcola_coefficiente_fiscale(forma, reg, add_com):
    if forma == "Regime Forfettario":
        return 0.0
    info_reg = regioni_db[reg]
    irap = info_reg["irap"]
    if forma == "Società di Capitali (S.r.l., S.p.A.)":
        return 0.24 + irap
    elif "medio" in forma:
        add_reg = (info_reg["add_reg_min"] + info_reg["add_reg_max"]) / 2.0
        return 0.35 + irap + add_reg + add_com
    elif "massimo" in forma:
        add_reg = info_reg["add_reg_max"]
        return 0.43 + irap + add_reg + add_com

coeff_fiscale = calcola_coefficiente_fiscale(forma_giuridica, regione, add_comunale_val)
st.sidebar.markdown("---")
st.sidebar.metric("Coefficiente Fiscale Unico (C2)", f"{coeff_fiscale * 100:.2f} %")

# ---------------------------------------------------------
# 2. BENEFICI ENERGETICI (TABELLA A 3 COLONNE DA EXCEL)
# ---------------------------------------------------------
st.header("💡 1. Benefici Energetici (Dati Impianto)")
st.markdown("*(I campi evidenziati in verde sono modificabili; i restanti seguono rigorosamente le formule del foglio Excel)*")

# Estrazione valori dai campi di input (verdi)
prod_impianto = st.session_state["prod_impianto"]         # B2
durata_noleggio = st.session_state["durata_noleggio"]     # C2
autoconsumo_pct = st.session_state["autoconsumo_pct"] / 100.0  # C4
costo_energia = st.session_state["costo_energia_pagata"]  # C6
prezzo_vendita = st.session_state["prezzo_energia_venduta"] # C10
cessione_pct = 1.0 - autoconsumo_pct                    # C8

# Calcoli esatti basati sul foglio Excel "Benefici Energetici"
prod_media_annuale = prod_impianto / durata_noleggio if durata_noleggio > 0 else 0  # D2
energia_autoconsumata = prod_media_annuale * autoconsumo_pct                         # D4
risparmio_autoconsumo = energia_autoconsumata * costo_energia                        # D6
energia_venduta = prod_media_annuale * cessione_pct                                  # D8
ricavo_vendita = energia_venduta * prezzo_vendita                                    # D10
totale_benefici = risparmio_autoconsumo + ricavo_vendita                             # D12

# Creazione della tabella a 3 colonne fedele al foglio Excel
col_t1, col_t2, col_t3 = st.columns([2, 2, 2])

with col_t1:
    st.subheader("Input & Autoconsumo")
    st.number_input("B2: Produzione Impianto (kWh)", step=500.0, key="prod_impianto")
    st.number_input("C4: Autoconsumo / Produzione (%)", step=5.0, key="autoconsumo_pct")
    st.number_input("C6: Costo Energia Pagata (€/kWh)", step=0.01, key="costo_energia_pagata")

with col_t2:
    st.subheader("Durata & Cessione")
    st.number_input("C2: Anni Durata Noleggio", step=1, key="durata_noleggio")
    st.metric("C8: Cessione EE / Produzione (%)", f"{cessione_pct * 100:.1f} %")
    st.number_input("C10: Prezzo Energia Venduta (€/kWh)", step=0.01, key="prezzo_energia_venduta")

with col_t3:
    st.subheader("Risultati Formule")
    st.metric("D2: Produzione Media Annuale", f"{prod_media_annuale:,.2f} kWh")
    st.metric("D4: Energia Autoconsumata", f"{energia_autoconsumata:,.2f} kWh")
    st.metric("D6: Risparmio in Autoconsumo", f"€ {risparmio_autoconsumo:,.2f}")
    st.metric("D8: Energia Venduta", f"{energia_venduta:,.2f} kWh")
    st.metric("D10: Ricavo dalla Vendita", f"€ {ricavo_vendita:,.2f}")

st.markdown(f"### 🎯 D12: Totale Benefici Energetici per Anno: **€ {totale_benefici:,.2f}**")
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
