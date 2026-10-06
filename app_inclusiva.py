import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# ==========================================
# 1. CONFIGURAZIONE PAGINA
# ==========================================
st.set_page_config(
    page_title="Palagiano Inclusiva",
    page_icon="💙",
    layout="wide",
    initial_sidebar_state="expanded"
)

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# ==========================================
# 2. MOTORI DATI
# ==========================================
@st.cache_data
def load_map_data():
    try:
        df = pd.read_csv('asset_palagiano.csv', sep=';', encoding='utf-8', on_bad_lines='skip')
        df['lat'] = df['lat'].astype(str).str.replace(',', '.', regex=False)
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = df['lon'].astype(str).str.replace(',', '.', regex=False)
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        df = df.dropna(subset=['lat', 'lon'])
        df['google_maps_url'] = "https://www.google.com/maps/dir/?api=1&destination=" + df['lat'].astype(str) + "," + df['lon'].astype(str)
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data
def load_istat_data():
    try:
        df = pd.read_csv('istat_palagiano.csv', sep=';', encoding='utf-8')
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data
def load_bandi_data():
    try:
        df = pd.read_csv('bandi_palagiano.csv', sep=';', encoding='utf-8', on_bad_lines='skip')
        return df
    except Exception:
        return pd.DataFrame()

if "tab_urgenti" not in st.session_state:
    st.session_state["tab_urgenti"] = {"selection": {"rows": []}}

# ==========================================
# 3. MOTORE LOGICO WELFARE
# ==========================================
def calcola_diritti_welfare(isee, figli, disabilita, legge_104):
    diritti = []
    
    if isee == "Sotto 9.360 €" and (figli > 0 or disabilita):
        diritti.append({
            "titolo": "Assegno di inclusione (ADI)",
            "importo": "Fino a 500€/mese + contributo affitto",
            "descrizione": "Sostegno economico statale introdotto dal DL 48/2023 per nuclei con minori o persone con disabilità.",
            "fonte": "Ministero del Lavoro e delle Politiche Sociali",
            "icona": "💶"
        })
    
    if isee == "Sotto 9.360 €" or (isee == "Tra 9.360 € e 15.000 €" and figli >= 4):
        diritti.append({
            "titolo": "Bonus sociale luce e gas",
            "importo": "Sconto diretto in bolletta",
            "descrizione": "Agevolazione tariffaria di ARERA riconosciuta in automatico con la DSU dell'ISEE.",
            "fonte": "ARERA",
            "icona": "⚡"
        })

    if figli > 0:
        importo_auu = "da 57€ a 199€ al mese per figlio"
        if disabilita:
            importo_auu = importo_auu + " (maggiorazioni previste per disabilità)"
        diritti.append({
            "titolo": "Assegno unico e universale",
            "importo": importo_auu,
            "descrizione": "Sostegno mensile per figli a carico, senza limiti di età in caso di disabilità.",
            "fonte": "INPS",
            "icona": "👶"
        })

    if disabilita and legge_104:
        diritti.append({
            "titolo": "Agevolazioni Legge 104 (Art.3 Comma 3)",
            "importo": "Permessi retribuiti e detrazioni fiscali",
            "descrizione": "3 giorni di permesso mensile retribuito, IVA al 4% per acquisto auto, detrazione 19% su spese mediche.",
            "fonte": "Agenzia delle Entrate",
            "icona": "♿"
        })
        
        diritti.append({
            "titolo": "Progetto Home Care Premium",
            "importo": "Contributo per assistenza domiciliare",
            "descrizione": "Finanziamento per l'assunzione di assistenti familiari per persone non autosufficienti.",
            "fonte": "INPS Gestione Dipendenti Pubblici",
            "icona": "🏡"
        })

    if figli > 0:
        if isee in ["Sotto 9.360 €", "Tra 9.360 € e 15.000 €", "Tra 15.000 € e 25.000 €"]:
            diritti.append({
                "titolo": "Bonus asilo nido",
                "importo": "Fino a 3.000€ annui",
                "descrizione": "Rimborso spese per rette di asili nido pubblici e privati autorizzati.",
                "fonte": "INPS",
                "icona": "🏫"
            })
            
    return diritti

# ==========================================
# 4. INTERFACCIA UTENTE (UI)
# ==========================================
def main():
    st.title("💙 Palagiano Inclusiva")
    st.markdown("### La centrale operativa per l'abbattimento delle barriere e lo sviluppo.")
    
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2070/2070086.png", width=80) 
    st.sidebar.header("🗺️ Aree di intervento")
    
    sezione = st.sidebar.radio("Scegli un modulo operativo:", [
        "1. Mappa barriere e servizi",
        "2. Sportello welfare e caregiver",
        "3. Imprese, lavoro e integrazione"
    ])

    # ---------------------------------------------------------
    # MODULO 1: MAPPA 
    # ---------------------------------------------------------
    if sezione == "1. Mappa barriere e servizi":
        st.info("**La nostra visione:** Non facciamo promesse, mappiamo problemi per risolverli. Seleziona una struttura dalla tabella per localizzarla sulla mappa.")
        df_mappa = load_map_data()
        
        if df_mappa.empty:
            st.error("🚨 ATTENZIONE: Il file 'asset_palagiano.csv' è vuoto o mancante.")
            return

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_tipo = st.selectbox("Filtra per categoria:", ["Tutti"] + sorted(df_mappa['type'].unique().tolist()))
        with col_f2:
            filtro_acc = st.selectbox("Filtra per stato accessibilità:", ["Tutti"] + sorted(df_mappa['accessibility'].dropna().unique().tolist()))

        df_filtrato = df_mappa.copy()
        if filtro_tipo != "Tutti":
            df_filtrato = df_filtrato[df_filtrato['type'] == filtro_tipo]
        if filtro_acc != "Tutti":
            df_filtrato = df_filtrato[df_filtrato['accessibility'] == filtro_acc]

        df_urgenti = df_filtrato[df_filtrato['accessibility'].isin(['Non Accessibile', 'Parzialmente Accessibile'])].copy()
        df_urgenti = df_urgenti.reset_index(drop=True) 
        
        selected_rows = st.session_state.tab_urgenti.get("selection", {}).get("rows", [])
        
        if selected_rows and len(df_urgenti) > 0:
            idx = selected_rows[0]
            center_lat = df_urgenti.loc[idx, 'lat']
            center_lon = df_urgenti.loc[idx, 'lon']
            zoom_level = 17 
        else:
            if not df_filtrato.empty:
                center_lat = df_filtrato['lat'].mean()
                center_lon = df_filtrato['lon'].mean()
            else:
                center_lat, center_lon = 40.578, 17.039 
            zoom_level = 14

        color_map = {'Accessibile': '#00CC96', 'Parzialmente Accessibile': '#FFA15A', 'Non Accessibile': '#EF553B'}

        fig = px.scatter_mapbox(
            df_filtrato, lat="lat", lon="lon", color="accessibility", color_discrete_map=color_map,
            hover_name="name", hover_data={"lat": False, "lon": False, "accessibility": True, "type": True, "notes": True},
            zoom=zoom_level, center={"lat": center_lat, "lon": center_lon}, height=500
        )
        
        fig.update_traces(marker=dict(size=15, opacity=0.9))
        fig.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0}, legend_title_text='Stato Struttura:', legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True, 'scrollZoom': False})
        
        st.markdown("---")
        st.markdown(f"#### 🚨 Piano di intervento prioritario ({len(df_urgenti)} strutture critiche)")
        
        if not df_urgenti.empty:
            df_table_view = df_urgenti[['name', 'type', 'accessibility', 'notes', 'google_maps_url', 'lat', 'lon']].copy()
            st.dataframe(
                df_table_view, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="tab_urgenti", 
                column_config={"name": "Nome struttura", "type": "Categoria", "accessibility": "Stato attuale", "notes": "Dettagli", "google_maps_url": st.column_config.LinkColumn("Navigazione GPS", display_text="Apri mappa 🗺️"), "lat": None, "lon": None}
            )

    # ---------------------------------------------------------
    # MODULO 2: SPORTELLO WELFARE 
    # ---------------------------------------------------------
    elif sezione == "2. Sportello welfare e caregiver":
        st.markdown("### 📊 Fotografia demografica (Dati reali)")
        df_istat = load_istat_data()
        if not df_istat.empty:
            pop_totale = df_istat['popolazione'].sum()
            over_65 = df_istat[df_istat['fascia_eta'].isin(['65-74 anni', '75+ anni'])]['popolazione'].sum()
            incidenza_anziani = (over_65 / pop_totale) * 100
            
            col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
            col_kpi1.metric("Popolazione residente", f"{pop_totale:,}".replace(',', '.'))
            col_kpi2.metric("Over 65 (Necessità assistenza)", f"{over_65:,}".replace(',', '.'))
            col_kpi3.metric("Incidenza anziani", f"{incidenza_anziani:.1f}%")

            fig_istat = px.bar(
                df_istat, x="popolazione", y="fascia_eta", orientation='h', color="categoria",
                title="Distribuzione popolazione per fascia d'età",
                labels={"popolazione": "Numero residenti", "fascia_eta": "Fascia d'età"},
                text="popolazione"
            )
            fig_istat.update_traces(textposition="inside")
            fig_istat.update_layout(margin={"l":0,"r":0,"t":40,"b":0})
            st.plotly_chart(fig_istat, use_container_width=True, config={'displayModeBar': False})
            st.caption("Fonte: ISTAT - Bilancio demografico permanente Palagiano.")

        st.markdown("---")
        st.markdown("### 👨‍‍👩‍👧‍👦 Calcolatore automatico dei diritti")
        
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                isee_input = st.selectbox(
                    "Fascia ISEE:", 
                    ["Non calcolato / Oltre 25.000 €", "Sotto 9.360 €", "Tra 9.360 € e 15.000 €", "Tra 15.000 € e 25.000 €"]
                )
                figli_input = st.number_input("Numero di figli a carico:", min_value=0, max_value=10, value=0, step=1)
            with col2:
                disabilita_input = st.toggle("Familiare con disabilità")
                legge_104_input = False
                if disabilita_input:
                    legge_104_input = st.checkbox("Certificazione Legge 104 (Art. 3 Comma 3)")
        
        if st.button("🔍 Calcola i diritti", type="primary"):
            risultati = calcola_diritti_welfare(isee_input, figli_input, disabilita_input, legge_104_input)
            if len(risultati) == 0:
                st.write("Al momento non risultano agevolazioni dirette calcolabili.")
            else:
                st.success(f"Individuate **{len(risultati)} agevolazioni** compatibili:")
                for diritto in risultati:
                    with st.expander(f"{diritto['icona']} **{diritto['titolo']}**"):
                        st.markdown(f"**Importo:** {diritto['importo']}")
                        st.markdown(f"**Descrizione:** {diritto['descrizione']}")
                        st.markdown(f"**Fonte:** {diritto['fonte']}")

    # ---------------------------------------------------------
    # MODULO 3: IMPRESE, LAVORO E INTEGRAZIONE 
    # ---------------------------------------------------------
    elif sezione == "3. Imprese, lavoro e integrazione":
        st.info("Applicativi operativi connessi ai database civici. Seleziona l'azione desiderata.")
        
        tab1, tab2 = st.tabs(["🚜 Motore di ricerca fondi e bandi", "🤝 Sportello multilingua (Ticket e orientamento)"])

        # --- TAB 1: MOTORE DI RICERCA BANDI (Connesso al CSV) ---
        with tab1:
            st.markdown("#### Ricerca fondi per le imprese e il terzo settore")
            df_bandi = load_bandi_data()
            
            if df_bandi.empty:
                st.warning("Nessun bando caricato nel database. Verifica il file 'bandi_palagiano.csv'.")
            else:
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    # Estrae i settori reali dal database in modo dinamico
                    settori_disponibili = ["Tutti i settori"] + sorted(df_bandi['settore'].unique().tolist())
                    settore_input = st.selectbox("Seleziona il settore:", settori_disponibili)
                
                with col_b2:
                    # Filtra gli obiettivi in base al settore scelto
                    if settore_input == "Tutti i settori":
                        obiettivi_disponibili = ["Tutti gli obiettivi"] + sorted(df_bandi['obiettivo'].unique().tolist())
                    else:
                        obiettivi_disponibili = ["Tutti gli obiettivi"] + sorted(df_bandi[df_bandi['settore'] == settore_input]['obiettivo'].unique().tolist())
                    
                    obiettivo_input = st.selectbox("Qual è l'obiettivo del finanziamento?", obiettivi_disponibili)
                
                if st.button("🔎 Cerca bandi attivi"):
                    df_risultati = df_bandi.copy()
                    if settore_input != "Tutti i settori":
                        df_risultati = df_risultati[df_risultati['settore'] == settore_input]
                    if obiettivo_input != "Tutti gli obiettivi":
                        df_risultati = df_risultati[df_risultati['obiettivo'] == obiettivo_input]
                        
                    st.markdown("---")
                    if not df_risultati.empty:
                        st.success(f"Trovati {len(df_risultati)} bandi compatibili con la ricerca:")
                        for _, row in df_risultati.iterrows():
                            st.markdown(f"""
                            <div style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 10px; border-left: 5px solid #005A9C;">
                                <h4 style="margin-top:0;">{row['titolo']}</h4>
                                <b>🎯 Obiettivo:</b> {row['obiettivo']}<br>
                                <b>💰 Agevolazione:</b> {row['importo']}<br>
                                <b>📅 Scadenza:</b> {row['scadenza']} | <b>🏛️ Ente:</b> {row['ente']}<br>
                                <p style="margin-top: 8px; font-size: 0.9em; color: #555;"><i>{row['descrizione']}</i></p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.warning("Nessun bando aperto corrisponde ai criteri. Il Comune attiverà allerte personalizzate all'uscita di nuovi fondi.")

        # --- TAB 2: SPORTELLO MULTILINGUA (Esteso) ---
        with tab2:
            st.markdown("#### Accesso ai servizi civici e tutela legale")
            st.write("Generazione ticket istantanea per abbattere barriere burocratiche, sanitarie e formative.")
            
            # Matrice di traduzione estesa
            matrice_servizi = {
                "Salute e Sanità (Tessera STP/ENI, Medico base)": {
                    "Italiano": "Salute e Sanità (Tessera STP/ENI)",
                    "English": "Health & Medical Care (STP/ENI Card)",
                    "Français": "Santé et Soins (Carte STP/ENI)",
                    "العربية": "الصحة والرعاية الطبية (بطاقة STP/ENI)",
                    "Română": "Sănătate și Asistență Medicală (Card STP/ENI)"
                },
                "Lavoro (Denuncia sfruttamento, Bandi assunzioni)": {
                    "Italiano": "Lavoro (Denuncia sfruttamento, Orientamento)",
                    "English": "Labor (Report exploitation, Job orientation)",
                    "Français": "Travail (Signaler exploitation, Orientation emploi)",
                    "العربية": "العمل (الإبلاغ عن الاستغلال، التوجيه الوظيفي)",
                    "Română": "Muncă (Raportați exploatarea, Orientare profesională)"
                },
                "Scuola (Iscrizione asilo, Corsi di italiano)": {
                    "Italiano": "Scuola (Iscrizione minori, Corsi lingua italiana)",
                    "English": "School (Child enrollment, Italian language courses)",
                    "Français": "École (Inscription enfants, Cours d'italien)",
                    "العربية": "المدرسة (تسجيل الأطفال، دورات اللغة الإيطالية)",
                    "Română": "Școală (Înscriere copii, Cursuri de limba italiană)"
                },
                "Anagrafe (Iscrizione residenza, Documenti)": {
                    "Italiano": "Anagrafe (Iscrizione residenza, Documenti)",
                    "English": "Registry (Residence registration, Documents)",
                    "Français": "État civil (Inscription résidence, Documents)",
                    "العربية": "السجل المدني (تسجيل الإقامة، المستندات)",
                    "Română": "Evidența Populației (Înregistrare reședință, Documente)"
                }
            }
            
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                lingua = st.selectbox("Seleziona la lingua di assistenza / Language:", ["Italiano", "English", "Français", "العربية", "Română"])
            with col_t2:
                # Estraiamo i servizi nella lingua scelta dinamicamente
                lista_voci_tradotte = [matrice_servizi[key][lingua] for key in matrice_servizi]
                servizio_scelto = st.selectbox("Area di intervento / Service:", lista_voci_tradotte)

            if st.button("🎫 Genera ticket di prenotazione sportello"):
                oggi = datetime.date.today()
                data_appuntamento = oggi + datetime.timedelta(days=2) 
                
                labels = {
                    "Italiano": {"tit": "RICEVUTA DI PRENOTAZIONE", "data": "Data", "ora": "Orario", "sportello": "Sportello Inclusione - Comune di Palagiano"},
                    "English": {"tit": "BOOKING RECEIPT", "data": "Date", "ora": "Time", "sportello": "Inclusion Office - Palagiano"},
                    "Français": {"tit": "REÇU DE RÉSERVATION", "data": "Date", "ora": "Heure", "sportello": "Bureau d'Inclusion - Palagiano"},
                    "العربية": {"tit": "إيصال الحجز", "data": "التاريخ", "ora": "الوقت", "sportello": "مكتب الإدماج - بالاجيانو"},
                    "Română": {"tit": "CHITANȚĂ REZERVARE", "data": "Data", "ora": "Ora", "sportello": "Biroul de Incluziune - Palagiano"}
                }
                l = labels[lingua]

                st.markdown("---")
                st.markdown(f"""
                <div style="border: 2px dashed #005A9C; border-radius: 10px; padding: 20px; background-color: #f8f9fa; text-align: center; color: #333;">
                    <h3 style="color: #005A9C; margin-top: 0;">{l['tit']}</h3>
                    <p style="font-size: 1.2em; font-weight: bold;">{servizio_scelto}</p>
                    <hr style="border-top: 1px solid #ccc;">
                    <p><b>{l['data']}:</b> {data_appuntamento.strftime('%d/%m/%Y')}</p>
                    <p><b>{l['ora']}:</b> 09:30 AM</p>
                    <p><b>📍 {l['sportello']}</b></p>
                    <p style="font-size: 0.8em; color: gray;">Ticket ID: PLG-{data_appuntamento.strftime('%Y%m%d')}-042</p>
                </div>
                """, unsafe_allow_html=True)

    # ==========================================
    # FIRMA
    # ==========================================
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray; font-size: 0.9em;'>
            <strong>Progetto "Palagiano Inclusiva"</strong><br>
            Architettura Dati: Francesco Pagliara - Data & Process Analyst.<br>
            <em>Piattaforma operativa per la gestione civica basata sui dati.</em>
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()