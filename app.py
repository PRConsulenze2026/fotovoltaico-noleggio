import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Simulatore Flusso di Cassa Fotovoltaico", layout="wide")

st.title("⚡ Simulatore Flusso di Cassa Fotovoltaico in Noleggio Operativo")

# ---------------------------------------------------------
# 1. ANAGRAFICA CLIENTE E DETRAZIONE FISCALE MEDIA
# ---------------------------------------------------------
st.sidebar.header("📋 Anagrafica Cliente & Inquadramento Fiscale")

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
add_comunale = st.sidebar.number_input("Addizionale Comunale (%)", value=0.8, step=0.1) / 100.0

# Calcolo del Coefficiente Unico Fiscale
def calcola_coefficiente_fiscale(forma, reg, add_com):
    if forma == "Regime Forfettario":
        return 0.0
    
    info_reg = regioni_db[reg]
    irap = info_reg["irap"]
    
    if forma == "Società di Capitali (S.r.l., S.p.A.)":
        # IRES (24%) + IRAP
        return 0.24 + irap
    elif "medio" in forma:
        # IRPEF (35%) + IRAP + Addizionale Regionale Media + Addizionale Comunale
        add_reg = (info_reg["add_reg_min"] + info_reg["add_reg_max"]) / 2.0
        return 0.35 + irap + add_reg + add_com
    elif "massimo" in forma:
        # IRPEF (43%) + IRAP + Addizionale Regionale Max + Addizionale Comunale
        add_reg = info_reg["add_reg_max"]
        return 0.43 + irap + add_reg + add_com

coeff_fiscale = calcola_coefficiente_fiscale(forma_giuridica, regione, add_comunale)

st.sidebar.markdown("---")
st.sidebar.metric("Coefficiente Fiscale Unico ($C2$)", f"{coeff_fiscale * 100:.2f} %")

# ---------------------------------------------------------
# 2. BENEFICI ENERGETICI & NOLEGGIO (INPUT UTENTE)
# ---------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("💡 1. Benefici Energetici (Dati Impianto)")
    prod_impianto = st.number_input("B2: Produzione Impianto (kWh)", value=14000.0, step=500.0)
    durata_noleggio = st.number_input("C2: Anni Durata Noleggio", value=7, step=1)
    autoconsumo_pct = st.number_input("C4: Autoconsumo / Produzione (%)", value=80.0, step=5.0) / 100.0
    costo_energia_pagata = st.number_input("C6: Costo Energia Attualmente Pagata (€/kWh)", value=0.25, step=0.01)
    prezzo_energia_venduta = st.number_input("C10: Prezzo Energia Venduta (€/kWh)", value=0.10, step=0.01)

with col2:
    st.subheader("💳 2. Parametri Noleggio Operativo")
    rata_mensile = st.number_input("A2: Rata Mensile Noleggio (€)", value=250.0, step=10.0)
    rata_bimestrale = rata_mensile * 2.0
    noleggio_annuale = rata_bimestrale * 6.0  # = rata_mensile * 12
    st.write(f"**A4 Rata Bimestrale:** € {rata_bimestrale:.2f}")
    st.write(f"**Noleggio Annuale (D2):** € {noleggio_annuale:.2f}")

# ---------------------------------------------------------
# 3. PERDITA DI ENERGIA (FOGLIO NASCOSTO - CALCOLO AUTOMATICO)
# ---------------------------------------------------------
prod_media_annuale = prod_impianto / durata_noleggio if durata_noleggio > 0 else 0
energia_autoconsumata_base = prod_media_annuale * autoconsumo_pct
cessione_pct = 1.0 - autoconsumo_pct
energia_venduta_base = prod_media_annuale * cessione_pct

anni = list(range(1, 26))
perdita_cumulata = [0.0] + [0.005 * (a - 1) for a in anni[1:]]

efficienza_residua = [1.0 - p for p in perdita_cumulata]
perdita_auto_kwh = [- (energia_autoconsumata_base * p) if i > 0 else 0 for i, p in enumerate(perdita_cumulata)]
auto_kwh_netto = [energia_autoconsumata_base + p for p in perdita_auto_kwh]

perdita_vendita_kwh = [- (energia_venduta_base * p) if i > 0 else 0 for i, p in enumerate(perdita_cumulata)]
vendita_kwh_netto = [energia_venduta_base + p for p in perdita_vendita_kwh]

risparmio_autoconsumo_eur = [kwh * costo_energia_pagata for kwh in auto_kwh_netto]
ricavo_vendita_eur = [kwh * prezzo_energia_venduta for kwh in vendita_kwh_netto]
totale_benefici_energetici = [r + v for r, v in zip(risparmio_autoconsumo_eur, ricavo_vendita_eur)]

# ---------------------------------------------------------
# 4. BENEFICI FISCALI
# ---------------------------------------------------------
beneficio_fiscale_mensile = rata_mensile * coeff_fiscale
beneficio_fiscale_mensile_arr = np.ceil(beneficio_fiscale_mensile)
beneficio_fiscale_annuale = beneficio_fiscale_mensile_arr * 12.0

# ---------------------------------------------------------
# 5. FLUSSI DI CASSA A 25 ANNI
# ---------------------------------------------------------
st.markdown("---")
st.subheader("📊 Flussi di Cassa Complessivi (25 Anni)")

col_opt1, col_opt2 = st.columns(2)
with col_opt1:
    manutenzione_default = st.number_input("Manutenzione Annuale (€)", value=-530.0, step=50.0)
with col_opt2:
    riscatto_default = st.number_input("Riscatto Finale (Anno 7) (€)", value=-500.0, step=50.0)

df_flussi = pd.DataFrame({
    "Anno": anni,
    "Benefici Energetici (€)": totale_benefici_energetici,
    "Benefici Fiscali (€)": [beneficio_fiscale_annuale if a <= durata_noleggio else np.nan for a in anni],
    "Noleggio (€)": [-noleggio_annuale if a <= durata_noleggio else np.nan for a in anni],
    "Manutenzione Annuale (€)": [manutenzione_default] * 25,
    "Riscatto (€)": [riscatto_default if a == durata_noleggio else np.nan for a in anni]
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
tot_energetici = sum(totale_benefici_energetici)
tot_fiscali = beneficio_fiscale_annuale * durata_noleggio
tot_noleggio = -noleggio_annuale * durata_noleggio
tot_manutenzione = manutenzione_default * 25
tot_riscatto = riscatto_default
tot_netto = tot_energetici + tot_fiscali + tot_noleggio + tot_manutenzione + tot_riscatto

m1, m2, m3, m4 = st.columns(4)
m1.metric("Totale Benefici Energetici", f"€ {tot_energetici:,.2f}")
m2.metric("Totale Benefici Fiscali", f"€ {tot_fiscali:,.2f}")
m3.metric("Totale Noleggio Operativo", f"€ {tot_noleggio:,.2f}")
m4.metric("Flusso Netto Cumulato a 25 Anni", f"€ {tot_netto:,.2f}")
