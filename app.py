import streamlit as st
import pandas as pd
import numpy as np
from html import escape as html_escape

# =========================================================
# CONFIGURAZIONE E STILE
# =========================================================
st.set_page_config(
    page_title="Eureka | Simulatore fotovoltaico",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
:root { --ink:#000000; --muted:#333333; --line:#dddddd; --brand:#111111; }
[data-testid="stAppViewContainer"] { background:#f5f7fb; }
[data-testid="stHeader"] { background:rgba(245,247,251,.88); }
.block-container { padding-top:1.7rem; padding-bottom:2.5rem; max-width:1500px; }
[data-testid="stSidebar"] { background:#111111; }
[data-testid="stSidebar"] * { color:#f3f7fb !important; }
[data-testid="stSidebar"] [data-baseweb="input"] input,
[data-testid="stSidebar"] [data-baseweb="select"] { color:#14243a !important; }
[data-testid="stSidebar"] [data-baseweb="input"] input { background:#fff !important; }
[data-testid="stMetric"] { background:#fff; border:1px solid var(--line); padding:16px 18px; border-radius:13px; box-shadow:0 2px 8px rgba(20,36,58,.035); }
[data-testid="stMetricLabel"] { color:var(--muted); font-weight:600; }
[data-testid="stMetricValue"] { color:var(--ink); }
section[data-testid="stSidebar"] .stButton button { width:100%; }
.stButton button[kind="primary"] { background:var(--brand); border-color:var(--brand); }
div[data-testid="stTabs"] button { font-weight:650; }
div[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:10px; }
div[data-testid="stAlert"] { border-radius:10px; }
.hero { background:#ffffff; color:#000000; border:1px solid #d6d6d6; padding:25px 28px; border-radius:16px; margin-bottom:20px; }
.hero h1 { color:#000000; font-size:1.8rem; margin:0 0 5px 0; }
.hero p { color:#000000; margin:0; }
.section-note { color:#66758a; font-size:.92rem; margin-top:-8px; }
.small-caption { color:#6b7a8e; font-size:.82rem; }
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
    "regione": "Puglia", "add_comunale": 0.8,
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

regioni_db = {
    "Abruzzo": {"irap": .0390, "add_reg_min": .0173, "add_reg_max": .0333},
    "Basilicata": {"irap": .0390, "add_reg_min": .0123, "add_reg_max": .0233},
    "Calabria": {"irap": .0482, "add_reg_min": .0203, "add_reg_max": .0333},
    "Campania": {"irap": .0497, "add_reg_min": .0203, "add_reg_max": .0333},
    "Emilia-Romagna": {"irap": .0390, "add_reg_min": .0133, "add_reg_max": .0227},
    "Friuli-Venezia Giulia": {"irap": .0390, "add_reg_min": .0123, "add_reg_max": .0123},
    "Lazio": {"irap": .0482, "add_reg_min": .0173, "add_reg_max": .0333},
    "Liguria": {"irap": .0390, "add_reg_min": .0123, "add_reg_max": .0333},
    "Lombardia": {"irap": .0390, "add_reg_min": .0123, "add_reg_max": .0173},
    "Marche": {"irap": .0390, "add_reg_min": .0123, "add_reg_max": .0173},
    "Molise": {"irap": .0482, "add_reg_min": .0173, "add_reg_max": .0333},
    "Piemonte": {"irap": .0390, "add_reg_min": .0162, "add_reg_max": .0333},
    "Puglia": {"irap": .0482, "add_reg_min": .0123, "add_reg_max": .0173},
    "Sardegna": {"irap": .0293, "add_reg_min": .0123, "add_reg_max": .0123},
    "Sicilia": {"irap": .0390, "add_reg_min": .0123, "add_reg_max": .0173},
    "Toscana": {"irap": .0390, "add_reg_min": .0142, "add_reg_max": .0173},
    "Trentino-Alto Adige": {"irap": .0346, "add_reg_min": .0123, "add_reg_max": .0123},
    "Umbria": {"irap": .0390, "add_reg_min": .0123, "add_reg_max": .0183},
    "Valle d'Aosta": {"irap": .0390, "add_reg_min": .0123, "add_reg_max": .0123},
    "Veneto": {"irap": .0390, "add_reg_min": .0123, "add_reg_max": .0123},
}

def euro(value):
    return f"€ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def numero(value, decimali=2):
    return f"{value:,.{decimali}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def reset_dati():
    for key, value in DEFAULTS.items():
        st.session_state[key] = value
    st.rerun()

def calcola_coefficiente_fiscale(forma, regione, add_com):
    if forma == "Regime Forfettario":
        return 0.0
    info = regioni_db[regione]
    if forma == "Società di Capitali (S.r.l., S.p.A.)":
        return 0.24 + info["irap"]
    return 0.35 + info["irap"] + info["add_reg_min"] + add_com

# =========================================================
# SIDEBAR: INPUT GUIDATI
# =========================================================
st.sidebar.markdown("# EUREKA SRL")
st.sidebar.caption("EUREKA SRL · SOCIETÀ BENEFIT")
st.sidebar.caption("Simulatore di convenienza fotovoltaica")
st.sidebar.text_input("Referente commerciale Eureka", key="referente_commerciale")
if st.sidebar.button("↺  Ripristina tutti i dati", use_container_width=True):
    reset_dati()
st.sidebar.divider()

with st.sidebar.expander("1 · Cliente e offerta", expanded=True):
    st.text_input("Cliente / ragione sociale", key="azienda", placeholder="Nome azienda")
    st.text_input("Indirizzo", key="indirizzo", placeholder="Via e numero civico")
    c1, c2 = st.columns(2)
    with c1:
        st.text_input("Città", key="citta")
        st.text_input("CAP", key="cap")
    with c2:
        st.text_input("Provincia", key="prov", max_chars=2)
        st.date_input("Data offerta", key="data_offerta")
    st.text_input("Protocollo offerta", key="protocollo")
    st.number_input("Potenza impianto (kWp)", min_value=0.0, step=.1, format="%.3f", key="potenza_kwp")

with st.sidebar.expander("2 · Produzione ed energia", expanded=True):
    st.number_input("Produzione totale stimata (kWh)", min_value=0.0, step=500.0, key="prod_impianto")
    st.number_input("Durata noleggio (anni)", min_value=1, max_value=25, step=1, key="durata_noleggio")
    st.number_input("Quota autoconsumo (%)", min_value=0.0, max_value=100.0, step=5.0, key="autoconsumo_pct")
    st.number_input("Costo energia acquistata (€/kWh)", min_value=0.0, step=.0001, format="%.5f", key="costo_energia_pagata")
    st.number_input("Quota energia ceduta (%)", min_value=0.0, max_value=100.0, step=1.0, key="cessione_pct")
    st.number_input("Prezzo energia venduta (€/kWh)", min_value=0.0, step=.0001, format="%.5f", key="prezzo_energia_venduta")
    if st.session_state.autoconsumo_pct + st.session_state.cessione_pct > 100:
        st.warning("Autoconsumo e cessione superano complessivamente il 100% della produzione.")

with st.sidebar.expander("3 · Noleggio e costi", expanded=True):
    st.number_input("Rata mensile (€)", min_value=0.0, step=10.0, key="rata_mensile")
    st.number_input("Manutenzione annuale (€)", min_value=0.0, step=50.0, key="manutenzione_default")
    st.number_input("Riscatto finale (€)", min_value=0.0, step=50.0, key="riscatto_default")

with st.sidebar.expander("4 · Parametri fiscali", expanded=False):
    forme = ["Società di Capitali (S.r.l., S.p.A.)", "Impresa individuale / Società di persone", "Regime Forfettario"]
    st.selectbox("Forma giuridica", forme, key="forma_giuridica")
    st.selectbox("Regione", list(regioni_db.keys()), key="regione")
    st.number_input("Addizionale comunale (%)", min_value=0.0, max_value=3.0, step=.1, format="%.2f", key="add_comunale")
    st.caption("Aliquote e beneficio fiscale sono parametri semplificati del modello: verificarli con il consulente fiscale.")

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
    st.session_state.add_comunale / 100,
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
st.markdown(f"""
<div class="hero">
  <h1>☀️ Simulatore fotovoltaico</h1>
  <p>Analisi economica del noleggio operativo · {html_escape(cliente)}</p>
</div>
""", unsafe_allow_html=True)

# KPI sintetici
k1, k2, k3, k4 = st.columns(4)
k1.metric("Produzione media annua", f"{numero(prod_media_annuale, 0)} kWh")
k2.metric("Benefici energetici annui · anno 1", euro(totale_benefici))
k3.metric("Canone annuo", euro(noleggio_annuale))
k4.metric("Flusso netto · anno 1", euro(df_flussi.loc[0, "Flusso netto (€)"]))

if st.session_state.azienda:
    st.caption(f"Offerta del {st.session_state.data_offerta.strftime('%d/%m/%Y')} · {st.session_state.citta} {st.session_state.prov} · Protocollo: {st.session_state.protocollo or 'non assegnato'}")
else:
    st.info("Compila i dati dell'offerta nel pannello laterale per personalizzare la simulazione.")

# Schede di navigazione
panoramica, energia, cassa, dettagli = st.tabs(["📌 Panoramica", "⚡ Analisi energetica", "📊 Flussi di cassa", "📄 Dati offerta"])

with panoramica:
    st.subheader("Sintesi economica")
    st.markdown("<p class='section-note'>Valori calcolati sulla base dei parametri inseriti nel pannello laterale.</p>", unsafe_allow_html=True)
    a, b, c = st.columns(3)
    a.metric("Risparmio da autoconsumo", euro(risparmio_autoconsumo))
    b.metric("Ricavo da energia ceduta", euro(ricavo_vendita))
    c.metric("Beneficio fiscale annuo stimato", euro(beneficio_fiscale_annuale))

    chart_df = df_flussi[["Anno", "Flusso netto (€)", "Cumulato (€)"]].set_index("Anno")
    st.markdown("#### Evoluzione economica su 25 anni")
    st.dataframe(chart_df, use_container_width=True)
    break_even = next((int(row["Anno"]) for _, row in df_flussi.iterrows() if row["Cumulato (€)"] >= 0), None)
    if break_even:
        st.success(f"Il flusso cumulato raggiunge un valore non negativo nell'anno {break_even}.")
    else:
        st.warning("Con i parametri attuali il flusso cumulato non diventa positivo nei 25 anni simulati.")
    st.caption("Il punto di pareggio è calcolato sul flusso cumulato del modello, senza attualizzazione finanziaria.")

with energia:
    st.subheader("Benefici energetici")
    e1, e2, e3 = st.columns(3)
    e1.metric("Energia autoconsumata", f"{numero(energia_autoconsumata)} kWh/anno")
    e2.metric("Energia ceduta", f"{numero(energia_venduta)} kWh/anno")
    e3.metric("Benefici complessivi", euro(totale_benefici))
    st.markdown("#### Perdite di Energia · prospetto completo (25 anni)")
    st.caption("10 colonne come nel foglio Excel 'Perdite di Energia'. Scorri orizzontalmente per vedere tutte le voci.")
    st.dataframe(
        df_perdita.style.format({
            "Efficienza residua (%)": "{:.2%}",
            "Perdita cumulata (%)": "{:.2%}",
            **{c: "{:,.2f}" for c in df_perdita.columns if c != "Anno" and "(%)" not in c},
        }), use_container_width=True, hide_index=True, height=900,
    )
    st.download_button("Esporta Perdite di Energia (CSV)",
        df_perdita.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
        file_name="Eureka_Perdite_di_Energia.csv", mime="text/csv")

with cassa:
    st.subheader("Flussi di cassa")
    f1, f2, f3 = st.columns(3)
    f1.metric("Rata mensile", euro(rata_mensile))
    f2.metric("Rata bimestrale", euro(rata_bimestrale))
    f3.metric("Noleggio annuale", euro(noleggio_annuale))
    st.markdown("#### Flussi di Cassa · prospetto completo (25 anni)")
    st.caption("8 colonne come nel foglio Excel 'Flussi di Cassa'. Scorri orizzontalmente per vedere tutte le voci.")
    st.dataframe(
        df_flussi.style.format({c: (lambda x: "" if pd.isna(x) else euro(x)) for c in df_flussi.columns if c != "Anno"}),
        use_container_width=True, hide_index=True, height=900,
    )
    st.download_button("Esporta Flussi di Cassa (CSV)",
        df_flussi.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
        file_name="Eureka_Flussi_di_Cassa.csv", mime="text/csv")

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
        st.write(f"Regione: {st.session_state.regione}")
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

st.divider()
st.header("Allegato al business plan · PDF e stampa")
st.caption("Documento preliminare con sezioni energetica ed economico-finanziaria, senza grafici.")

def _fmt_num(v):
    return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def _safe(v):
    return html_escape(str(v or "—"))

logo_file = Path(__file__).with_name("logo_eureka.png")

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
    if logo_file.exists():
        from reportlab.platypus import Image
        from PIL import Image as PILImage
        with PILImage.open(logo_file) as im:
            w, h = im.size
        width = 50*mm
        story.append(Image(str(logo_file), width=width, height=width*h/w))
        story.append(Spacer(1, 3*mm))
    story.extend([
        Paragraph("<b>EUREKA SRL</b>", styles["EurekaTitle"]),
        Paragraph("SOCIETÀ BENEFIT · RISPARMIO ENERGETICO", styles["EurekaSmall"]),
        Paragraph("Via Kufstein, 1 · 38121 Trento (TN) · P.IVA 02326350226", styles["EurekaSmall"]),
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
    add_table("2 · Perdite di Energia — 25 annualità", en, [11,22,22,27,26,27,26,26,26,30])
    story.append(PageBreak())
    add_table("3 · Flussi di Cassa — 25 annualità (€)", ca, [12,29,27,23,28,20,25,26])
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph("Simulazione indicativa. Verificare ipotesi tecniche, contrattuali e fiscali con professionisti competenti.", styles["EurekaSmall"]))
    doc.build(story)
    return buffer.getvalue()

def genera_html_stampa():
    en, ca = _tabelle_allegato()
    def tabella(rows):
        return "<table><thead><tr>" + "".join(f"<th>{_safe(x)}</th>" for x in rows[0]) + "</tr></thead><tbody>" + "".join(
            "<tr>" + "".join(f"<td>{_safe(x)}</td>" for x in row) + "</tr>" for row in rows[1:]
        ) + "</tbody></table>"
    import base64
    img = ""
    if logo_file.exists():
        img = '<img class="logo" src="data:image/png;base64,' + base64.b64encode(logo_file.read_bytes()).decode() + '">'
    dati = "".join(f"<p><b>{_safe(k)}:</b> {_safe(v)}</p>" for k,v in _dati_allegato())
    return f"""<!doctype html><html lang="it"><head><meta charset="utf-8">
    <title>Eureka · Allegato al business plan</title>
    <style>
    body{{font-family:Arial,sans-serif;color:#000;margin:22px;}}
    .logo{{max-width:190px;max-height:85px;object-fit:contain;}}
    h1{{font-size:22px;margin:6px 0 0;}} h2{{font-size:17px;margin-top:28px;}}
    .sub{{font-size:12px;margin:3px 0 8px;}} .dati p{{margin:3px 0;font-size:12px;}}
    table{{width:100%;border-collapse:collapse;font-size:10px;table-layout:fixed;}}
    th{{background:#000;color:#fff;}} th,td{{border:1px solid #aaa;padding:5px;overflow-wrap:anywhere;}}
    tbody tr:nth-child(even){{background:#f0f0f0;}}
    td:not(:first-child){{text-align:right;}}
    .print{{background:#111;color:white;padding:10px 18px;border:0;cursor:pointer;}}
    .page-break{{break-before:page;page-break-before:always;}}
    thead{{display:table-header-group;}} tr{{break-inside:avoid;page-break-inside:avoid;}}
    @media print{{.print{{display:none}} @page{{size:A3 landscape;margin:12mm}} body{{margin:0}}}}
    </style></head><body>
    <button class="print" onclick="window.print()">Stampa</button>
    {img}<h1>EUREKA SRL</h1><div class="sub">SOCIETÀ BENEFIT · RISPARMIO ENERGETICO</div>
    <div class="sub">Via Kufstein, 1 · 38121 Trento (TN) · P.IVA 02326350226</div>
    <h2>Allegato preliminare al business plan</h2><div class="dati">{dati}</div>
    <h2>2 · Perdite di Energia — 25 annualità</h2>{tabella(en)}
    <section class="page-break"><h2>3 · Flussi di Cassa — 25 annualità (€)</h2>{tabella(ca)}</section>
    <p style="font-size:10px">Simulazione indicativa. Verificare ipotesi tecniche, contrattuali e fiscali.</p>
    </body></html>"""

col_pdf, col_stampa = st.columns(2)
with col_pdf:
    st.download_button("Scarica PDF (tabelle complete)", genera_pdf(), file_name="Eureka_Allegato_Business_Plan.pdf",
                       mime="application/pdf", use_container_width=True)
with col_stampa:
    st.download_button("Scarica versione per stampa", genera_html_stampa().encode("utf-8"),
                       file_name="Eureka_Stampa.html", mime="text/html", use_container_width=True)
st.caption("Per stampare: apri il file HTML scaricato nel browser e premi Stampa. Impaginazione A3 orizzontale per leggibilità.")
