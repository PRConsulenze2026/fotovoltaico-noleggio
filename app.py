from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import time
import json
import re
import unicodedata
from datetime import date, datetime
from html import escape as html_escape

# =========================================================
# CONFIGURAZIONE E STILE
# =========================================================
st.set_page_config(
    page_title="Eureka | Simulatore fotovoltaico",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
:root { --ink:#f6f7f9; --muted:#c4cbd5; --line:#3c4654; --brand:#566f89; }
[data-testid="stAppViewContainer"], [data-testid="stMain"] { background:#101820; color:#f6f7f9; }
[data-testid="stHeader"] { background:rgba(16,24,32,.96); }
.block-container { padding-top:1.7rem; padding-bottom:2.5rem; max-width:1500px; }
[data-testid="stSidebar"] { display:none; }
[data-testid="collapsedControl"] { display:none; }
[data-testid="stSidebar"] * { color:#f6f7f9; }
[data-testid="stSidebar"] input, [data-testid="stSidebar"] [data-baseweb="select"] { background:#253341; color:#fff; }
[data-testid="stSidebar"] input { color:#fff !important; }
[data-testid="stMetric"] { background:#1c2935; border:1px solid var(--line); padding:16px 18px; border-radius:13px; }
[data-testid="stMetricLabel"] { color:#c4cbd5; font-weight:600; }
[data-testid="stMetricValue"] { color:#fff; }
section[data-testid="stSidebar"] .stButton button { width:100%; }
.stButton button[kind="primary"] { background:#426482; border-color:#6383a0; color:#fff; }
div[data-testid="stTabs"] button { font-weight:650; }
div[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:10px; }
div[data-testid="stAlert"] { border-radius:10px; }
.hero { background:#1c2935; color:#f6f7f9; border:1px solid #435163; padding:25px 28px; border-radius:16px; margin-bottom:20px; }
.hero h1 { color:#fff; font-size:1.8rem; margin:0 0 5px 0; }
.hero p { color:#d9e0e8; margin:0; }
.section-note { color:#c4cbd5; font-size:.92rem; margin-top:-8px; }
.small-caption { color:#c4cbd5; font-size:.82rem; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# DATI DI DEFAULT E FUNZIONI
# =========================================================
DEFAULTS = {
    "potenza_kwp": 0.0, "azienda": "", "indirizzo": "", "citta": "", "referente_commerciale": "",
    "cap": "", "prov": "", "protocollo": "", "data_offerta": pd.Timestamp.today().date(),
    "prod_impianto": 0.0, "durata_noleggio": 7, "autoconsumo_pct": 0.0,
    "costo_energia_pagata": 0.0, "cessione_pct": 0.0,
    "prezzo_energia_venduta": 0.0, "rata_mensile": 0.0,
    "manutenzione_default": 0.0, "riscatto_default": 0.0,
    "forma_giuridica": "Società di Capitali (S.r.l., S.p.A.)",
    "regione": None, "aliquota_totale": 0.0, "aliquota_modificata": False,
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

ALIQUOTE_FORMA = {'Regime Forfettario': 0.0, 'Società di Capitali (S.r.l., S.p.A.)': 0.24, 'Ditta Individuale / S.n.c. (Scaglione IRPEF medio)': 0.35, 'Ditta Individuale / S.n.c. (Scaglione IRPEF massimo)': 0.43}
ALIQUOTE_IRPEF_REGIONALI = {'Abruzzo': 0.0173, 'Basilicata': 0.0123, 'Calabria': 0.0203, 'Campania': 0.0203, 'Emilia-Romagna': 0.0133, 'Friuli-Venezia Giulia': 0.0123, 'Lazio': 0.0173, 'Liguria': 0.0123, 'Lombardia': 0.0123, 'Marche': 0.0123, 'Molise': 0.0173, 'Piemonte': 0.0162, 'Puglia': 0.0123, 'Sardegna': 0.0123, 'Sicilia': 0.0123, 'Toscana': 0.0142, 'Umbria': 0.0123, "Valle d'Aosta": 0.0123, 'Veneto': 0.0123, 'Trentino-Alto Adige (Trento)': 0.0123, 'Trentino-Alto Adige (Bolzano)': 0.0123}
ALIQUOTE_IRAP_REGIONALI = {'Abruzzo': 0.039, 'Basilicata': 0.039, 'Calabria': 0.0482, 'Campania': 0.0497, 'Emilia-Romagna': 0.039, 'Friuli-Venezia Giulia': 0.039, 'Lazio': 0.0482, 'Liguria': 0.039, 'Lombardia': 0.039, 'Marche': 0.039, 'Molise': 0.0482, 'Piemonte': 0.039, 'Puglia': 0.0482, 'Sardegna': 0.0293, 'Sicilia': 0.039, 'Toscana': 0.039, 'Trentino-Alto Adige (Bolzano)': 0.0268, 'Trentino-Alto Adige (Trento)': 0.0346, 'Umbria': 0.039, "Valle d'Aosta": 0.039, 'Veneto': 0.039}

# Valori iniziali tratti dal foglio Excel "Tabelle Aliquote".
# Le modifiche sono mantenute nella sessione Streamlit, non nel file Excel.
TABELLE_ALIQUOTE = {
    "Forma giuridica": ALIQUOTE_FORMA,
    "IRPEF regionale minima": ALIQUOTE_IRPEF_REGIONALI,
    "IRAP regionale ordinaria": ALIQUOTE_IRAP_REGIONALI,
}
for nome_tabella, valori_iniziali in TABELLE_ALIQUOTE.items():
    chiave = "tabella_" + nome_tabella
    if chiave not in st.session_state:
        st.session_state[chiave] = dict(valori_iniziali)

def aliquota_corrente(tabella, voce):
    return st.session_state["tabella_" + tabella][voce]

def calcola_aliquota_totale(forma, regione):
    if not regione:
        return 0.0
    base = aliquota_corrente("Forma giuridica", forma)
    if forma == "Regime Forfettario":
        return 0.0
    irpef = aliquota_corrente("IRPEF regionale minima", regione)
    irap = aliquota_corrente("IRAP regionale ordinaria", regione)
    return round(100 * (base + irpef + irap), 2)

def sincronizza_aliquota():
    st.session_state.aliquota_totale = calcola_aliquota_totale(
        st.session_state.forma_giuridica, st.session_state.regione)
    st.session_state.aliquota_modificata = False

def aggiorna_aliquota_manuale():
    st.session_state.aliquota_modificata = True

def modifica_blocco_aliquota(chiave):
    if st.session_state["bloccata_" + chiave]:
        st.session_state.pop("scadenza_" + chiave, None)
    else:
        st.session_state["scadenza_" + chiave] = time.time() + 300

def aggiorna_valore_aliquota(tabella, voce, chiave):
    st.session_state["tabella_" + tabella][voce] = (
        st.session_state["valore_" + chiave] / 100.0)
    sincronizza_aliquota()

def riga_aliquota(tabella, voce, indice):
    chiave = f"{['forma','irpef','irap'][['Forma giuridica','IRPEF regionale minima','IRAP regionale ordinaria'].index(tabella)]}_{indice}"
    blocco = "bloccata_" + chiave
    scadenza = "scadenza_" + chiave
    valore = "valore_" + chiave
    if blocco not in st.session_state:
        st.session_state[blocco] = True
    if not st.session_state[blocco] and time.time() >= st.session_state.get(scadenza, 0):
        st.session_state[blocco] = True
        st.session_state.pop(scadenza, None)
    if valore not in st.session_state:
        st.session_state[valore] = round(aliquota_corrente(tabella, voce) * 100, 4)
    nome_col, aliquota_col, protezione_col = st.columns([5, 2, 2], vertical_alignment="center")
    nome_col.write(voce.upper() if tabella != "Forma giuridica" else voce)
    aliquota_col.number_input(
        f"Aliquota (%) · {voce}", min_value=0.0, max_value=100.0,
        step=0.01, format="%.4f", key=valore,
        disabled=st.session_state[blocco], label_visibility="collapsed",
        on_change=aggiorna_valore_aliquota, args=(tabella, voce, chiave))
    protezione_col.checkbox(
        f"Protetta · {voce}", key=blocco,
        on_change=modifica_blocco_aliquota, args=(chiave,))
    if not st.session_state[blocco]:
        rimanenti = max(0, int(st.session_state[scadenza] - time.time()))
        protezione_col.caption(f"Riblocco tra {rimanenti // 60}:{rimanenti % 60:02d}")

@st.fragment(run_every="5s")
def mostra_tabelle_aliquote():
    st.caption("Ogni aliquota è protetta per impostazione predefinita. "
               "Togli il flag della singola riga per modificarla; "
               "la protezione torna automaticamente entro 5 minuti.")
    for tabella in TABELLE_ALIQUOTE:
        st.markdown(f"#### {tabella}")
        for indice, voce in enumerate(st.session_state["tabella_" + tabella]):
            riga_aliquota(tabella, voce, indice)
        st.divider()
    st.caption("Le variazioni si applicano ai calcoli della sessione corrente. "
               "La protezione impedisce la modifica accidentale, non è un controllo di accesso.")

def euro(value, decimali=2):
    return f"€ {value:,.{decimali}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def numero(value, decimali=2):
    return f"{value:,.{decimali}f}".replace(",", "X").replace(".", ",").replace("X", ".")

CAMPI_MAIUSCOLI = {'indirizzo', 'referente_commerciale', 'cap', 'prov', 'protocollo', 'azienda', 'citta'}

def converti_in_maiuscolo(chiave):
    valore = st.session_state.get(chiave)
    if isinstance(valore, str):
        st.session_state[chiave] = valore.upper()

def cancella_tutti_i_dati():
    # Callback eseguito prima della creazione dei widget: svuota i dati inseriti
    # e conserva i valori predefiniti necessari al funzionamento del simulatore.
    for key, value in DEFAULTS.items():
        st.session_state[key] = value.upper() if key in CAMPI_MAIUSCOLI and isinstance(value, str) else value
    # La somma fiscale predefinita deve corrispondere alle aliquote attive.
    st.session_state["aliquota_totale"] = 0.0  # Regione vuota: nessuna aliquota cliente applicata
    st.session_state["aliquota_modificata"] = False

def calcola_coefficiente_fiscale(forma, regione, aliquota_totale_percentuale):
    if forma == "Regime Forfettario":
        return 0.0
    return aliquota_totale_percentuale / 100.0


# =========================================================
# SALVATAGGIO E RIAPERTURA SIMULAZIONI (JSON LOCALE)
# =========================================================
def esporta_simulazione():
    dati = {}
    for chiave, predefinito in DEFAULTS.items():
        valore = st.session_state.get(chiave, predefinito)
        dati[chiave] = valore.isoformat() if isinstance(valore, (date, datetime)) else valore
    tabelle = {nome: dict(st.session_state["tabella_" + nome]) for nome in TABELLE_ALIQUOTE}
    return json.dumps({"formato": "eureka-simulazione", "versione": 1,
                       "dati": dati, "tabelle_aliquote": tabelle},
                      ensure_ascii=False, indent=2).encode("utf-8")

def carica_simulazione():
    file = st.session_state.get("file_simulazione")
    if file is None:
        st.session_state["esito_caricamento"] = ("error", "Seleziona prima un file JSON.")
        return
    try:
        payload = json.loads(file.getvalue().decode("utf-8"))
        if not isinstance(payload, dict) or payload.get("formato") != "eureka-simulazione":
            raise ValueError("Il file non è una simulazione Eureka.")
        dati = payload.get("dati")
        if not isinstance(dati, dict):
            raise ValueError("Dati mancanti.")
        nuovi = {}
        for chiave, default in DEFAULTS.items():
            v = dati.get(chiave, default)
            if chiave == "data_offerta":
                v = date.fromisoformat(v) if isinstance(v, str) else default
            elif chiave == "regione":
                if v is not None and v not in ALIQUOTE_IRPEF_REGIONALI:
                    raise ValueError("Regione non valida.")
            elif chiave == "forma_giuridica":
                if v not in ALIQUOTE_FORMA:
                    raise ValueError("Forma giuridica non valida.")
            elif isinstance(default, str):
                if not isinstance(v, str):
                    raise ValueError(f"Testo non valido: {chiave}")
                if chiave in CAMPI_MAIUSCOLI:
                    v = v.upper()
            elif isinstance(default, bool):
                if not isinstance(v, bool):
                    raise ValueError(f"Flag non valido: {chiave}")
            elif isinstance(default, int):
                v = int(v)
            elif isinstance(default, float):
                v = float(v)
                if not 0 <= v <= 1e12:
                    raise ValueError(f"Numero non valido: {chiave}")
            nuovi[chiave] = v
        if not 1 <= nuovi["durata_noleggio"] <= 25:
            raise ValueError("Durata del noleggio non valida.")
        for chiave in ("autoconsumo_pct", "cessione_pct", "aliquota_totale"):
            if not 0 <= nuovi[chiave] <= 100:
                raise ValueError(f"Percentuale non valida: {chiave}")
        originali_importati = payload.get("tabelle_aliquote", {})
        if not isinstance(originali_importati, dict):
            raise ValueError("Tabelle non valide.")
        nuove_tabelle = {}
        for nome, originali in TABELLE_ALIQUOTE.items():
            valori = originali_importati.get(nome, originali)
            if not isinstance(valori, dict) or set(valori) != set(originali):
                raise ValueError(f"Tabella non valida: {nome}")
            valori = {k: float(v) for k, v in valori.items()}
            if any(not 0 <= v <= 1 for v in valori.values()):
                raise ValueError(f"Aliquota non valida: {nome}")
            nuove_tabelle[nome] = valori
    except (ValueError, TypeError, UnicodeDecodeError, OverflowError) as exc:
        st.session_state["esito_caricamento"] = ("error", f"Caricamento non riuscito: {exc}")
        return
    # Callback: prima dell'istanziazione dei widget.
    for chiave, valore in nuovi.items():
        st.session_state[chiave] = valore
    for nome, valori in nuove_tabelle.items():
        st.session_state["tabella_" + nome] = valori
        prefisso = {"Forma giuridica": "forma",
                    "IRPEF regionale minima": "irpef",
                    "IRAP regionale ordinaria": "irap"}[nome]
        for indice, valore in enumerate(valori.values()):
            chiave = f"{prefisso}_{indice}"
            st.session_state["valore_" + chiave] = round(valore * 100, 4)
            st.session_state["bloccata_" + chiave] = True
            st.session_state.pop("scadenza_" + chiave, None)
    st.session_state["esito_caricamento"] = ("success", "Simulazione caricata correttamente.")

# =========================================================
# SIDEBAR: INPUT GUIDATI
# =========================================================
# I campi di inserimento sono ora nella scheda Inserimento Dati.

# =========================================================
# CALCOLI (logica del modello originale mantenuta)
# =========================================================
prod_impianto = float(st.session_state.prod_impianto)
durata_noleggio = int(st.session_state.durata_noleggio)
autoconsumo_pct = st.session_state.autoconsumo_pct / 100
costo_energia = float(st.session_state.costo_energia_pagata)
prezzo_vendita = float(st.session_state.prezzo_energia_venduta)
cessione_pct = st.session_state.cessione_pct / 100

prod_media_annuale = prod_impianto / durata_noleggio if durata_noleggio else 0
energia_autoconsumata = prod_media_annuale * autoconsumo_pct
risparmio_autoconsumo = energia_autoconsumata * costo_energia
energia_venduta = prod_media_annuale * cessione_pct
ricavo_vendita = energia_venduta * prezzo_vendita
totale_benefici = risparmio_autoconsumo + ricavo_vendita

anni = list(range(1, 26))
perdita_cumulata = [0.0 if a == 1 else round(.005 * (a - 1), 3) for a in anni]
efficienza_residua = [1.0 - p for p in perdita_cumulata]
perdita_auto_kwh = [-(energia_autoconsumata * p) for p in perdita_cumulata]
auto_kwh_netto = [energia_autoconsumata + p for p in perdita_auto_kwh]
perdita_vendita_kwh = [-(energia_venduta * p) for p in perdita_cumulata]
vendita_kwh_netto = [energia_venduta + p for p in perdita_vendita_kwh]
risparmio_auto_eur = [v * costo_energia for v in auto_kwh_netto]
ricavo_vendita_eur = [v * prezzo_vendita for v in vendita_kwh_netto]
totale_benefici_perdita = [risparmio_auto_eur[i] + ricavo_vendita_eur[i] for i in range(25)]

df_perdita = pd.DataFrame({
    "Anno": anni,
    "Efficienza residua (%)": efficienza_residua,
    "Perdita cumulata (%)": perdita_cumulata,
    "Autoconsumo perso (kWh)": perdita_auto_kwh,
    "Autoconsumo netto (kWh)": auto_kwh_netto,
    "Energia ceduta persa (kWh)": perdita_vendita_kwh,
    "Energia ceduta netta (kWh)": vendita_kwh_netto,
    "Risparmio autoconsumo (€)": risparmio_auto_eur,
    "Ricavo vendita (€)": ricavo_vendita_eur,
    "Benefici energetici (€)": totale_benefici_perdita,
})

coeff_fiscale = calcola_coefficiente_fiscale(
    st.session_state.forma_giuridica,
    st.session_state.regione,
    st.session_state.aliquota_totale,
)
rata_mensile = float(st.session_state.rata_mensile)
beneficio_fiscale_mensile = rata_mensile * coeff_fiscale
beneficio_fiscale_annuale = np.ceil(beneficio_fiscale_mensile) * 12
rata_bimestrale = rata_mensile * 2
noleggio_annuale = rata_bimestrale * 6
manutenzione = float(st.session_state.manutenzione_default)
riscatto = float(st.session_state.riscatto_default)

df_flussi = pd.DataFrame({
    "Anno": anni,
    "Benefici energetici (€)": totale_benefici_perdita,
    "Benefici fiscali (€)": [beneficio_fiscale_annuale if a <= durata_noleggio else np.nan for a in anni],
    "Noleggio (€)": [-noleggio_annuale if a <= durata_noleggio else np.nan for a in anni],
    "Manutenzione (€)": [-manutenzione] * 25,
    "Riscatto (€)": [-riscatto if a == durata_noleggio else np.nan for a in anni],
})
colonne_flusso = ["Benefici energetici (€)", "Benefici fiscali (€)", "Noleggio (€)", "Manutenzione (€)", "Riscatto (€)"]
df_flussi["Flusso netto (€)"] = df_flussi[colonne_flusso].sum(axis=1)
df_flussi["Cumulato (€)"] = df_flussi["Flusso netto (€)"].cumsum()

# =========================================================
# AREA PRINCIPALE
# =========================================================
cliente = st.session_state.azienda.strip() or "Nuova simulazione"
# Intestazione compatta: informazioni a sinistra, referente commerciale a destra.
st.markdown("""
<style>
div[data-testid="stVerticalBlockBorderWrapper"]:has(.eureka-hero-marker) {
    background:#1c2935;
    border:none;
    border-radius:16px;
}
.eureka-hero-title {font-size:1.8rem; font-weight:750; color:#fff; line-height:1.25; margin:0 0 6px;}
.eureka-hero-subtitle {font-size:.95rem; color:#d9e0e8; margin:0;}
</style>
""", unsafe_allow_html=True)
for campo_maiuscolo in CAMPI_MAIUSCOLI:
    if campo_maiuscolo in st.session_state:
        converti_in_maiuscolo(campo_maiuscolo)

with st.container(border=False):
    hero_sx, hero_dx = st.columns([2.3, 1], gap="large", vertical_alignment="center")
    with hero_sx:
        st.markdown(
            '<div class="eureka-hero-marker">'
            '<div class="eureka-hero-title">☀️ Simulatore fotovoltaico</div>'
            f'<p class="eureka-hero-subtitle">Analisi economica del noleggio operativo · {html_escape(cliente)}</p>'
            '</div>',
            unsafe_allow_html=True,
        )
    with hero_dx:
        # Logo aziendale già caricato nel repository GitHub: nessun nuovo file richiesto.
        # Supporta anche il nome originale dell'immagine fornita.
        logo_aziendale = next(
            (p for nome in ("logo_eureka.png", "Logo 100x100.png", "Logo.png")
             if (p := Path(__file__).with_name(nome)).is_file()),
            None,
        )
        logo_col, nome_col = st.columns([1, 3], gap="small", vertical_alignment="center")
        with logo_col:
            if logo_aziendale is not None:
                st.image(str(logo_aziendale), width=78)
        with nome_col:
            st.markdown(
                '<div style="color:#fff;font-weight:800;font-size:23px;line-height:1.15;white-space:nowrap;">'
                'EUREKA SRL</div>'
                '<div style="color:#d9e0e8;font-weight:600;font-size:14px;letter-spacing:.035em;white-space:nowrap;">'
                'SOCIETÀ BENEFIT</div>',
                unsafe_allow_html=True,
            )
        st.text_input("Referente Commerciale", key="referente_commerciale", placeholder="Inserisci il referente", on_change=converti_in_maiuscolo, args=("referente_commerciale",))

# KPI sintetici
k1, k2, k3, k4 = st.columns(4)
k1.metric("Produzione media annua", f"{numero(prod_media_annuale, 0)} kWh")
k2.metric("Benefici energetici annui · anno 1", euro(totale_benefici))
k3.metric("Canone annuo", euro(noleggio_annuale))
k4.metric("Flusso netto · anno 1", euro(df_flussi.loc[0, "Flusso netto (€)"]))

if st.session_state.azienda:
    st.caption(f"Offerta del {st.session_state.data_offerta.strftime('%d/%m/%Y')} · {st.session_state.citta} {st.session_state.prov} · Protocollo: {st.session_state.protocollo or 'non assegnato'}")
else:
    st.info("Compila i dati dell'offerta nella scheda Inserimento Dati per personalizzare la simulazione.")

# Schede di navigazione
inserimento, dettagli, energia, noleggio, cassa, tabelle_aliquote, archivio, documenti = st.tabs(["📝 Inserimento Dati", "📄 Dati offerta", "⚡ Analisi energetica", "💶 Noleggio", "📊 Flussi di cassa", "📋 Tabelle Aliquote", "💾 Archivio Simulazioni", "📄 🖨️ PDF e Stampa"])

with inserimento:
    st.subheader("Inserimento Dati")
    st.caption("Compila i dati del cliente, della produzione, del noleggio e i parametri fiscali.")
    st.button("🗑️  Cancella tutti i Dati", use_container_width=True, on_click=cancella_tutti_i_dati)
    st.divider()

    with st.expander("1 · Anagrafica Cliente", expanded=True):
        st.text_input("Ragione Sociale", key="azienda", placeholder="Nome azienda", on_change=converti_in_maiuscolo, args=("azienda",))
        st.text_input("Indirizzo", key="indirizzo", placeholder="Via e numero civico", on_change=converti_in_maiuscolo, args=("indirizzo",))
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Città", key="citta", on_change=converti_in_maiuscolo, args=("citta",))
            st.text_input("CAP", key="cap", on_change=converti_in_maiuscolo, args=("cap",))
        with c2:
            st.text_input("Provincia", key="prov", max_chars=2, on_change=converti_in_maiuscolo, args=("prov",))
            st.date_input("Data offerta", key="data_offerta", format="DD/MM/YYYY")
        st.selectbox("Regione", list(st.session_state["tabella_IRPEF regionale minima"].keys()), key="regione", index=None, placeholder="SELEZIONA UNA REGIONE",
                     format_func=lambda nome: nome.upper(), on_change=sincronizza_aliquota)
        st.text_input("Protocollo offerta", key="protocollo", on_change=converti_in_maiuscolo, args=("protocollo",))
        st.number_input("Potenza impianto (kWp)", min_value=0.0, step=.1, format="%.3f", key="potenza_kwp")

    with st.expander("2 · Produzione ed energia", expanded=True):
        st.number_input("Produzione totale stimata (kWh)", min_value=0.0, step=500.0, key="prod_impianto")
        st.number_input("Durata noleggio (anni)", min_value=1, max_value=25, step=1, key="durata_noleggio")
        st.number_input("Quota autoconsumo (%)", min_value=0.0, max_value=100.0, step=5.0, key="autoconsumo_pct")
        st.number_input("Costo energia acquistata (€/kWh)", min_value=0.0, step=.0001, format="%.5f", key="costo_energia_pagata")
        st.number_input("Quota energia ceduta (%)", min_value=0.0, max_value=100.0, step=1.0, key="cessione_pct")
        st.number_input("Prezzo energia venduta (€/kWh)", min_value=0.0, step=.0001, format="%.5f", key="prezzo_energia_venduta")
        if st.session_state.autoconsumo_pct + st.session_state.cessione_pct > 100:
            st.warning("Autoconsumo e cessione superano complessivamente il 100% della produzione.")

    with st.expander("3 · Noleggio e costi", expanded=True):
        st.number_input("Rata mensile (€)", min_value=0.0, step=10.0, key="rata_mensile")
        st.number_input("Manutenzione annuale (€)", min_value=0.0, step=50.0, key="manutenzione_default")
        st.number_input("Riscatto finale (€)", min_value=0.0, step=50.0, key="riscatto_default")

    with st.expander("4 · Parametri fiscali", expanded=False):
        st.selectbox("Forma giuridica", list(st.session_state["tabella_Forma giuridica"].keys()), key="forma_giuridica",
                     on_change=sincronizza_aliquota)
        regione_selezionata = st.session_state.regione
        forma_selezionata = st.session_state.forma_giuridica
        regione_irpef_selezionata = regione_selezionata
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Aliquota Fiscale Stimata", f"{aliquota_corrente('Forma giuridica', forma_selezionata)*100:.2f}%" if regione_selezionata else "—")
        col_b.metric("IRPEF Regionale · Aliquota Minima", f"{aliquota_corrente('IRPEF regionale minima', regione_irpef_selezionata)*100:.2f}%" if regione_irpef_selezionata else "—")
        col_c.metric("IRAP Regionale · Aliquota Ordinaria", f"{aliquota_corrente('IRAP regionale ordinaria', regione_selezionata)*100:.2f}%" if regione_selezionata else "—")
        st.number_input("Aliquota Totale (%)", min_value=0.0, max_value=100.0,
                        step=0.01, format="%.2f", key="aliquota_totale",
                        on_change=aggiorna_aliquota_manuale,
                        help="Valore proposto: somma delle tre aliquote indicate; puoi modificarlo manualmente.")
        proposta = calcola_aliquota_totale(forma_selezionata, regione_selezionata)
        if regione_selezionata:
            st.caption(f"Valore automatico secondo il foglio Tabelle Aliquote: {proposta:.2f}%. "
                       "La modifica manuale resta valida finché non cambi forma giuridica o regione.")
        else:
            st.caption("Seleziona una regione nell'Anagrafica Cliente per visualizzare "
                       "le aliquote fiscali e calcolare l'Aliquota Totale.")
        st.caption("Le aliquote del file Excel sono indicative: la somma non rappresenta necessariamente "
                   "l'imposta effettiva applicabile. Verificare con il consulente fiscale.")

with energia:
    st.subheader("Benefici Energetici")
    # Riproduzione delle sei sezioni a quattro colonne del foglio Excel
    # "Benefici Energetici": titolo del risultato, due basi di calcolo e valore.
    sezioni_benefici = [
        (
            ["", "Produzione Impianto/kWh", "Anni Durata Noleggio", "kWh"],
            ["Produzione Media Annuale", numero(prod_impianto), str(durata_noleggio), numero(prod_media_annuale)],
        ),
        (
            ["", "Produzione Media Annuale", "Autoconsumo/Produzione di Energia in %", "kWh"],
            ["Energia Autoconsumata", numero(prod_media_annuale), numero(autoconsumo_pct * 100, 2) + "%", numero(energia_autoconsumata)],
        ),
        (
            ["", "Energia Autoconsumata", "Costo Energia Attualmente Pagata in kWh", "€."],
            ["Risparmio in Autoconsumo", numero(energia_autoconsumata), euro(costo_energia, 5), euro(risparmio_autoconsumo)],
        ),
        (
            ["", "Produzione Media Annuale", "Cessione EE/Produzione di Energia in %", "kWh"],
            ["Energia Venduta", numero(prod_media_annuale), numero(cessione_pct * 100, 2) + "%", numero(energia_venduta)],
        ),
        (
            ["", "Energia Venduta", "Prezzo Energia Venduta in kWh", "€."],
            ["Ricavo dalla Vendita", numero(energia_venduta), euro(prezzo_vendita, 5), euro(ricavo_vendita)],
        ),
        (
            ["", "Risparmio in Autoconsumo", "Ricavo dalla Vendita", "€."],
            ["Totale Benefici Energetici per Anno", euro(risparmio_autoconsumo), euro(ricavo_vendita), euro(totale_benefici)],
        ),
    ]
    righe_benefici = []
    for intestazioni, valori in sezioni_benefici:
        righe_benefici.append("<tr class='eureka-benefici-head'>" + "".join(
            f"<th>{html_escape(t)}</th>" for t in intestazioni
        ) + "</tr>")
        righe_benefici.append("<tr class='eureka-benefici-val'>" + "".join(
            f"<td>{html_escape(str(v))}</td>" for v in valori
        ) + "</tr>")
    st.markdown("""
    <style>
    table.eureka-benefici {width:100%; border-collapse:collapse; table-layout:fixed; color:#f6f7f9; font-size:clamp(10px,0.9vw,13px);}
    .eureka-benefici th,.eureka-benefici td {border:1px solid #526172; padding:10px 8px; overflow-wrap:anywhere; vertical-align:middle;}
    .eureka-benefici th {background:#354352; color:white; text-align:center; line-height:1.35; font-weight:700;}
    .eureka-benefici td {background:#1b2935; text-align:right;}
    .eureka-benefici td:first-child {text-align:left; font-weight:700;}
    .eureka-benefici th:first-child,.eureka-benefici td:first-child {width:29%;}
    .eureka-benefici th:nth-child(2),.eureka-benefici td:nth-child(2) {width:22%;}
    .eureka-benefici th:nth-child(3),.eureka-benefici td:nth-child(3) {width:34%;}
    .eureka-benefici th:nth-child(4),.eureka-benefici td:nth-child(4) {width:15%;}
    </style>
    <table class="eureka-benefici"><tbody>""" + "".join(righe_benefici) + "</tbody></table>", unsafe_allow_html=True)
    st.markdown("#### Perdite di Energia (25 anni)")
    intestazioni_energia_excel = {
        "Anno": "Anno",
        "Efficienza residua (%)": "Efficienza Residua Stimata (%)",
        "Perdita cumulata (%)": "Perdita di Energia Cumulata (%)",
        "Autoconsumo perso (kWh)": "Energia Autoconsumata (Perdita in kWh)",
        "Autoconsumo netto (kWh)": "Energia Autoconsumata (kWh)",
        "Energia ceduta persa (kWh)": "Energia Venduta (Perdita in kWh)",
        "Energia ceduta netta (kWh)": "Energia Venduta (kWh)",
        "Risparmio autoconsumo (€)": "Risparmio in Autoconsumo (€)",
        "Ricavo vendita (€)": "Ricavo dalla Vendita (€)",
        "Benefici energetici (€)": "Totale Benefici Energetici per Anno (€)",
    }
    # Tabella HTML a larghezza piena: intestazioni multilinea e 25 righe visibili.
    # A differenza di st.dataframe, le intestazioni possono andare a capo.
    intestazioni_multiriga = [
        "Anno",
        "Efficienza Residua<br>Stimata (%)",
        "Perdita di Energia<br>Cumulata (%)",
        "Energia Autoconsumata<br>(Perdita in kWh)",
        "Energia Autoconsumata<br>(kWh)",
        "Energia Venduta<br>(Perdita in kWh)",
        "Energia Venduta<br>(kWh)",
        "Risparmio in<br>Autoconsumo (€)",
        "Ricavo dalla<br>Vendita (€)",
        "Totale Benefici Energetici<br>per Anno (€)",
    ]

    def _cella_energia(valore, nome_colonna):
        if pd.isna(valore):
            return "—"
        if nome_colonna == "Anno":
            return str(int(valore))
        if "(%)" in nome_colonna:
            return numero(float(valore) * 100, 2) + "%"
        return numero(float(valore), 2)

    righe_energia = []
    for _, riga in df_perdita.iterrows():
        celle = "".join(
            f"<td>{_cella_energia(riga[colonna], colonna)}</td>"
            for colonna in df_perdita.columns
        )
        righe_energia.append(f"<tr>{celle}</tr>")

    intestazioni_html = "".join(f"<th scope='col'>{titolo}</th>" for titolo in intestazioni_multiriga)
    tabella_energia_html = f"""
    <style>
      .eureka-energia {{
        width:100%; table-layout:fixed; border-collapse:collapse;
        color:#f6f7f9; font-size:clamp(9px, 0.75vw, 12px);
        font-variant-numeric:tabular-nums;
      }}
      .eureka-energia th {{
        background:#354352; color:#fff; font-weight:700;
        white-space:normal; overflow-wrap:anywhere; word-break:normal;
        line-height:1.35; height:88px; padding:8px 3px;
        text-align:center; vertical-align:middle;
        border:1px solid #718092;
      }}
      .eureka-energia td {{
        padding:7px 3px; text-align:right; white-space:nowrap;
        border:1px solid #465363; overflow:hidden;
      }}
      .eureka-energia th:first-child, .eureka-energia td:first-child {{
        width:4.3%; text-align:center;
      }}
      .eureka-energia th:nth-child(2), .eureka-energia th:nth-child(3) {{
        width:9%;
      }}
      .eureka-energia th:nth-child(4), .eureka-energia th:nth-child(6) {{
        width:11.5%;
      }}
      .eureka-energia th:nth-child(5), .eureka-energia th:nth-child(7) {{
        width:10%;
      }}
      .eureka-energia th:nth-child(8), .eureka-energia th:nth-child(9) {{
        width:10.5%;
      }}
      .eureka-energia th:nth-child(10) {{ width:13.7%; }}
      .eureka-energia tbody tr:nth-child(odd) {{ background:#1b2935; }}
      .eureka-energia tbody tr:nth-child(even) {{ background:#253442; }}
      .eureka-energia tbody tr:hover {{ background:#364a5d; }}
      @media (max-width:900px) {{
        .eureka-energia {{ font-size:9px; }}
        .eureka-energia th {{ padding:6px 2px; }}
        .eureka-energia td {{ padding:6px 2px; }}
      }}
    </style>
    <table class="eureka-energia" aria-label="Perdite di Energia, 25 anni">
      <thead><tr>{intestazioni_html}</tr></thead>
      <tbody>{''.join(righe_energia)}</tbody>
    </table>
    """
    st.markdown(tabella_energia_html, unsafe_allow_html=True)
    st.download_button("Esporta Perdite di Energia (CSV)",
        df_perdita.rename(columns=intestazioni_energia_excel).to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
        file_name="Eureka_Perdite_di_Energia.csv", mime="text/csv")

with noleggio:
    st.subheader("Noleggio")
    f1, f2, f3 = st.columns(3)
    f1.metric("Rata mensile", euro(rata_mensile))
    f2.metric("Rata bimestrale", euro(rata_bimestrale))
    f3.metric("Noleggio annuale", euro(noleggio_annuale))

with cassa:
    st.markdown("#### Flussi di Cassa · prospetto completo (25 anni)")
    st.caption("8 colonne come nel foglio Excel 'Flussi di Cassa'. Scorri orizzontalmente per vedere tutte le voci.")
    st.dataframe(
        df_flussi.style.format({c: (lambda x: "" if pd.isna(x) else euro(x)) for c in df_flussi.columns if c != "Anno"}),
        use_container_width=True, hide_index=True, height=900,
    )
    st.download_button("Esporta Flussi di Cassa (CSV)",
        df_flussi.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
        file_name="Eureka_Flussi_di_Cassa.csv", mime="text/csv")

with tabelle_aliquote:
    st.subheader("Tabelle Aliquote")
    st.caption("Valori di riferimento dal foglio Excel «Tabelle Aliquote».")
    mostra_tabelle_aliquote()

with dettagli:
    st.subheader("Riepilogo dell'offerta")
    left, right = st.columns(2)
    with left:
        st.markdown("**Cliente**")
        st.write(st.session_state.azienda or "—")
        st.write(st.session_state.indirizzo or "—")
        st.write(f"{st.session_state.cap} {st.session_state.citta} ({st.session_state.prov})")
        st.write(f"Protocollo: {st.session_state.protocollo or '—'}")
        st.write(f"Data: {st.session_state.data_offerta.strftime('%d/%m/%Y')}")
    with right:
        st.markdown("**Parametri tecnici ed economici**")
        st.write(f"Potenza: {numero(st.session_state.potenza_kwp, 3)} kWp")
        st.write(f"Durata noleggio: {durata_noleggio} anni")
        st.write(f"Forma giuridica: {st.session_state.forma_giuridica}")
        st.write(f"Regione: {st.session_state.regione or '—'}")
        st.write(f"Coefficiente fiscale applicato: {coeff_fiscale:.2%}")
    st.info("I risultati sono simulazioni indicative basate sui dati inseriti. La sezione fiscale richiede verifica professionale e non costituisce un parere tributario.")

st.divider()
st.caption("Eureka Srl Società Benefit · Simulatore di supporto commerciale · Verificare sempre ipotesi tecniche, contrattuali e fiscali prima di formulare un'offerta definitiva.")


# =========================================================
# ALLEGATO BUSINESS PLAN: PDF E STAMPA
# =========================================================
from io import BytesIO
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4

def _fmt_num(v):
    return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def _safe(v):
    return html_escape(str(v or "—"))

logo_file = next((p for nome in ("logo_eureka.png", "Logo 100x100.png", "Logo.png")
                  if (p := Path(__file__).with_name(nome)).is_file()), None)

def _dati_allegato():
    return [
        ("Cliente", st.session_state.azienda or "—"),
        ("Indirizzo", st.session_state.indirizzo or "—"),
        ("Località", f"{st.session_state.cap} {st.session_state.citta} ({st.session_state.prov})"),
        ("Protocollo", st.session_state.protocollo or "—"),
        ("Data", st.session_state.data_offerta.strftime("%d/%m/%Y")),
        ("Potenza impianto", f"{_fmt_num(st.session_state.potenza_kwp)} kWp"),
        ("Durata noleggio", f"{durata_noleggio} anni"),
        ("Referente commerciale", st.session_state.referente_commerciale or "—"),
        ("Regione cliente", (st.session_state.regione or "—").upper()),
        ("Aliquota Totale", f"{st.session_state.aliquota_totale:.2f}%"),
    ]

# Le intestazioni riprendono le dieci e le otto colonne dei due fogli Excel.
ENERGIA_COLONNE = [
    ("Anno", "Anno"),
    ("Efficienza Residua Stimata (%)", "Efficienza residua (%)"),
    ("Perdita di Energia Cumulata (%)", "Perdita cumulata (%)"),
    ("Energia Autoconsumata (Perdita in kWh)", "Autoconsumo perso (kWh)"),
    ("Energia Autoconsumata (kWh)", "Autoconsumo netto (kWh)"),
    ("Energia Venduta (Perdita in kWh)", "Energia ceduta persa (kWh)"),
    ("Energia Venduta (kWh)", "Energia ceduta netta (kWh)"),
    ("Risparmio in Autoconsumo (€)", "Risparmio autoconsumo (€)"),
    ("Ricavo dalla Vendita (€)", "Ricavo vendita (€)"),
    ("Totale Benefici Energetici per Anno (€)", "Benefici energetici (€)"),
]
CASSA_COLONNE = [
    ("Anno", "Anno"),
    ("Benefici Energetici (€)", "Benefici energetici (€)"),
    ("Benefici Fiscali (€)", "Benefici fiscali (€)"),
    ("Noleggio (€)", "Noleggio (€)"),
    ("Manutenzione Annuale (€)", "Manutenzione (€)"),
    ("Riscatto (€)", "Riscatto (€)"),
    ("Flusso Netto (€)", "Flusso netto (€)"),
    ("Cumulato (€)", "Cumulato (€)"),
]

def _tabelle_allegato():
    def costruisci(df, colonne):
        rows = [[nome for nome, _ in colonne]]
        for _, r in df.iterrows():
            values = []
            for nome, campo in colonne:
                val = r[campo]
                if pd.isna(val):
                    values.append("")  # Celle vuote come nel foglio Flussi di Cassa
                elif campo == "Anno":
                    values.append(str(int(val)))
                elif "(%)" in nome:
                    values.append(_fmt_num(val * 100) + "%")
                else:
                    values.append(_fmt_num(val))
            rows.append(values)
        return rows
    return costruisci(df_perdita, ENERGIA_COLONNE), costruisci(df_flussi, CASSA_COLONNE)

def genera_pdf():
    from reportlab.lib.pagesizes import landscape, A3
    from reportlab.platypus import PageBreak
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A3),
                            leftMargin=14*mm, rightMargin=14*mm,
                            topMargin=14*mm, bottomMargin=14*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="EurekaTitle", parent=styles["Heading1"],
                              textColor=colors.black, fontSize=15, spaceAfter=7))
    styles.add(ParagraphStyle(name="EurekaSmall", parent=styles["Normal"],
                              fontSize=9, leading=12, textColor=colors.black))
    styles.add(ParagraphStyle(name="EurekaHeader", parent=styles["Normal"],
                              fontSize=7, leading=8, textColor=colors.white,
                              alignment=TA_CENTER))
    story = []
    # Intestazione compatta: logo a sinistra, nome e sottotitolo a destra.
    intestazione_testi = [
        Paragraph("<b>EUREKA SRL</b>", styles["EurekaTitle"]),
        Paragraph("SOCIETÀ BENEFIT · RISPARMIO ENERGETICO", styles["EurekaSmall"]),
        Paragraph("Via Kufstein, 1 · 38121 Trento (TN) · P.IVA 02326350226", styles["EurekaSmall"]),
    ]
    if logo_file is not None:
        from reportlab.platypus import Image
        from PIL import Image as PILImage
        with PILImage.open(logo_file) as im:
            w, h = im.size
        # Mantiene le proporzioni, entro 22 x 22 mm.
        fattore = min((22*mm)/w, (22*mm)/h)
        logo = Image(str(logo_file), width=w*fattore, height=h*fattore)
        intestazione = Table([[logo, intestazione_testi]],
                             colWidths=[28*mm, landscape(A3)[0]-28*mm-28*mm],
                             hAlign="LEFT")
        intestazione.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (0, 0), 4*mm),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(intestazione)
    else:
        story.extend(intestazione_testi)
    story.extend([
        Spacer(1, 7*mm),
        Paragraph("Allegato preliminare al business plan", styles["EurekaTitle"]),
    ])
    for k, v in _dati_allegato():
        story.append(Paragraph(f"<b>{html_escape(k)}:</b> {html_escape(str(v))}", styles["EurekaSmall"]))
    story.append(Spacer(1, 6*mm))

    en, ca = _tabelle_allegato()
    usable_width = landscape(A3)[0] - 28*mm
    def add_table(title, data, widths):
        story.append(Paragraph(title, styles["EurekaTitle"]))
        headers = [Paragraph(html_escape(str(h)), styles["EurekaHeader"]) for h in data[0]]
        table = Table([headers] + data[1:], colWidths=[usable_width * w / sum(widths) for w in widths],
                      repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0),(-1,0),colors.black),
            ("ROWBACKGROUNDS", (0,1),(-1,-1),[colors.white, colors.HexColor("#f1f1f1")]),
            ("TEXTCOLOR", (0,1),(-1,-1),colors.black),
            ("GRID", (0,0),(-1,-1),0.25,colors.HexColor("#aaaaaa")),
            ("FONTNAME", (0,1),(-1,-1),"Helvetica"),
            ("FONTSIZE", (0,1),(-1,-1),8),
            ("ALIGN", (1,1),(-1,-1),"RIGHT"),
            ("VALIGN", (0,0),(-1,-1),"MIDDLE"),
            ("TOPPADDING",(0,0),(-1,-1),5),
            ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ]))
        story.append(table)
    add_table("Perdite di Energia — 25 annualità", en, [11,22,22,27,26,27,26,26,26,30])
    story.append(PageBreak())
    add_table("Flussi di Cassa — 25 annualità", ca, [12,29,27,23,28,20,25,26])
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph("Simulazione indicativa. Verificare ipotesi tecniche, contrattuali e fiscali con professionisti competenti.", styles["EurekaSmall"]))
    def numero_pagina(canvas, documento):
        canvas.saveState()
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(landscape(A3)[0]-14*mm, 9*mm, f"Pagina {documento.page}")
        canvas.restoreState()
    doc.build(story, onFirstPage=numero_pagina, onLaterPages=numero_pagina)
    return buffer.getvalue()

def nome_file_cliente():
    nome = st.session_state.get("azienda", "").strip()
    nome = unicodedata.normalize("NFKD", nome)
    nome = "".join(c for c in nome if not unicodedata.combining(c))
    nome = re.sub(r"[^A-Za-z0-9_-]+", "_", nome).strip("_-")
    return (nome[:90] or "CLIENTE_SENZA_NOME")

with archivio:
    st.header("💾 Archivio Simulazioni")
    st.markdown("#### Salva o riapri una simulazione")
    st.caption("Salva i dati sul computer in formato JSON e riaprili in seguito, "
               "comprese le aliquote eventualmente modificate.")
    col_salva, col_apri = st.columns(2)
    with col_salva:
        st.download_button("💾 Salva simulazione", data=esporta_simulazione(),
                           file_name=f"{nome_file_cliente()}.json", mime="application/json",
                           use_container_width=True)
    with col_apri:
        st.file_uploader("Seleziona il file della simulazione (.json)",
                         type=["json"], key="file_simulazione", max_upload_size=200)
        st.button("📂 Apri simulazione", on_click=carica_simulazione,
                  use_container_width=True)
    if "esito_caricamento" in st.session_state:
        livello, messaggio = st.session_state.pop("esito_caricamento")
        (st.success if livello == "success" else st.error)(messaggio)

with documenti:
    st.header("📄 🖨️ PDF e Stampa")
    st.markdown("#### Allegato al business plan · PDF e stampa")
    st.caption("Documento preliminare con sezioni energetica ed economico-finanziaria, senza grafici. "
               "Il PDF contiene il logo Eureka, le tabelle complete e le pagine numerate.")
    pdf_documento = genera_pdf()
    col_pdf, col_stampa = st.columns(2)
    with col_pdf:
        st.download_button("📄 Scarica PDF", data=pdf_documento,
                           file_name=f"{nome_file_cliente()}_Business_Plan.pdf",
                           mime="application/pdf", use_container_width=True)
    with col_stampa:
        st.download_button("🖨️ Prepara PDF per stampa", data=pdf_documento,
                           file_name=f"{nome_file_cliente()}_Stampa.pdf",
                           mime="application/pdf", use_container_width=True)
    st.info("Per stampare in modo affidabile: premi **Prepara PDF per stampa**, "
            "apri il PDF scaricato e scegli **Stampa** (oppure premi Ctrl+P). "
            "Formato A3 orizzontale. Il browser non apre automaticamente la stampa "
            "dall'interno di Streamlit.")
