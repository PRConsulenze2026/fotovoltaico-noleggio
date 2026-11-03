import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Simulatore Flusso di Cassa Fotovoltaico", layout="wide")

st.title("⚡ Simulatore Flusso di Cassa Fotovoltaico in Noleggio Operativo")

# ---------------------------------------------------------
# 0. ANAGRAFICA & DATI OFFERTA
# ---------------------------------------------------------
st.header("📄 Anagrafica e Dati Offerta")

col1, col2 = st.columns(2)
with col1:
    azienda = st.text_input("Azienda / Cliente", value="Nome Cliente S.r.l.")
    indirizzo = st.text_input("Indirizzo", value="Via Roma 1")
with col2:
    citta = st.text_input("Città", value="Milano")
    potenza_kwp = st.number_input("Potenza Impianto (kWp)", value=30.0, step=1.0)

st.markdown("---")

# ---------------------------------------------------------
# 1. INQUADRAMENTO FISCALE
# ---------------------------------------------------------
st.sidebar.header("📋 Inquadramento Fiscale")

regioni_db = {
    "Abruzzo": {"irap": 0.0390, "add_reg": 0.0200},
    "Campania": {"irap": 0.0497, "add_reg": 0.0203},
    "Lazio": {"irap": 0.0482, "add_reg": 0.0173},
    "Lombardia": {"irap": 0.0390, "add_reg": 0.0123},
    "Piemonte": {"irap": 0.0390, "add_reg": 0.0162},
    "Puglia": {"irap": 0.0482, "add_reg": 0.0123},
    "Veneto": {"irap": 0.0390, "add_reg": 0.0123},
}

regione = st.sidebar.selectbox("Regione", list(regioni_db.keys()))
forma_giuridica = st.sidebar.selectbox(
    "Forma Giuridica",
    ["Società di Capitali (S.r.l./S.p.A.)", "Ditta Individuale / S.n.c.", "Regime Forfettario"]
)

def calcola_coeff(forma, reg):
    if forma == "Regime Forfettario":
        return 0.0
    irap = regioni_db[reg]["irap"]
    add_reg = regioni_db[reg]["add_reg"]
    if "Capitali" in forma:
        return 0.24 + irap
    else:
        return 0.35 + irap + add_reg

coeff_fiscale = calcola_coeff(forma_giuridica, regione)
st.sidebar.metric("Coefficiente Fiscale (C2)", f"{coeff_fiscale * 100:.2f} %")

# ---------------------------------------------------------
# 2. BENEFICI ENERGETICI & NOLEGGIO
# ---------------------------------------------------------
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("💡 Dati Energetici")
    prod_impianto = st.number_input("Produzione Annua (kWh)", value=14000.0, step=500.0)
    durata_noleggio = st.number_input("Durata Noleggio (Anni)", value=7, step=1)
    autoconsumo_pct = st.slider("Autoconsumo (%)", 10, 100, 80) / 100.0
    costo_energia = st.number_input("Costo Energia (€/kWh)", value=0.25, step=0.01)
    prezzo_vendita = st.number_input("Prezzo Energia Venduta (€/kWh)", value=0.10, step=0.01)

with col_b:
    st.subheader("💳 Parametri Noleggio")
    rata_mensile = st.number_input("Rata Mensile (€)", value=250.0, step=10.0)
    noleggio_annuale = rata_mensile * 12.0
    st.write(f"**Noleggio Annuale:** € {noleggio_annuale:,.2f}")

# ---------------------------------------------------------
# 3. CALCOLI E FLUSSI A 25 ANNI
# ---------------------------------------------------------
prod_media = prod_impianto / durata_noleggio if durata_noleggio > 0 else 0
auto_base = prod_media * autoconsumo_pct
vendita_base = prod_media * (1.0 - autoconsumo_pct)

anni = list(range(1, 26))
flussi_netti = []
cumulato = 0
dati_tabella = []

beneficio_fiscale_annuo = np.ceil(rata_mensile * coeff_fiscale) * 12.0

for a in anni:
    perdita = 0.005 * (a - 1) if a > 1 else 0.0
    kwh_auto_netto = auto_base * (1.0 - perdita)
    kwh_vendita_netto = vendita_base * (1.0 - perdita)
    
    beneficio_en = (kwh_auto_netto * costo_energia) + (kwh_vendita_netto * prezzo_vendita)
    beneficio_fis = beneficio_fiscale_annuo if a <= durata_noleggio else 0.0
    costo_nol = -noleggio_annuale if a <= durata_noleggio else 0.0
    manutenzione = -530.0
    riscatto = -500.0 if a == durata_noleggio else 0.0
    
    netto_anno = beneficio_en + beneficio_fis + costo_nol + manutenzione + riscatto
    cumulato += netto_anno
    
    dati_tabella.append({
        "Anno": a,
        "Benefici Energetici (€)": beneficio_en,
        "Benefici Fiscali (€)": beneficio_fis if beneficio_fis > 0 else 0,
        "Noleggio (€)": costo_nol if costo_nol < 0 else 0,
        "Manutenzione (€)": manutenzione,
        "Riscatto (€)": riscatto if riscatto < 0 else 0,
        "Flusso Netto (€)": netto_anno,
        "Cumulato (€)": cumulato
    })

df = pd.DataFrame(dati_tabella)

st.markdown("---")
st.subheader("📊 Tabella Flussi di Cassa (25 Anni)")
st.dataframe(df.style.format("{:,.2f}"), use_container_width=True)

# Totali
tot_netto = df["Flusso Netto (€)"].sum()
st.metric("Flusso Netto Cumulato Totale (25 Anni)", f"€ {tot_netto:,.2f}")
