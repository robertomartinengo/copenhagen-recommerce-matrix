import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Copenhagen Re-Commerce Matrix",
    page_icon="♻️",
    layout="wide"
)

API_URL = "http://127.0.0.1:8000"

st.title("♻️ Copenhagen Re-Commerce Matrix")
st.markdown("##### Location Intelligence & Circular Fashion Analytics (Greater Copenhagen & Frederiksberg)")

# ---------------------------------------------------------
# Sidebar: Controlli Simulazione What-If
# ---------------------------------------------------------
st.sidebar.header("🎛️ Simulazione Pesi CPI")
st.sidebar.markdown("Modifica i pesi della formula per testare scenari strategici in tempo reale.")

w_supply = st.sidebar.slider("Peso Supply (Rifiuti/Tessile)", 0.0, 1.0, 0.40, 0.05)
w_demo = st.sidebar.slider("Peso Demografia (Gen Z / Income)", 0.0, 1.0, 0.35, 0.05)
w_gap = st.sidebar.slider("Peso Vuoto di Mercato", 0.0, 1.0, 0.25, 0.05)

total_w = round(w_supply + w_demo + w_gap, 2)

if total_w != 1.0:
    st.sidebar.error(f"⚠️ La somma dei pesi deve fare 1.0 (Attuale: {total_w})")
else:
    st.sidebar.success("✅ Pesi bilanciati correttamente (100%)")

# Coordinate per la mappa dei quartieri
DISTRICT_COORDS = {
    "DK-1000": {"lat": 55.6761, "lon": 12.5683},  # Indre By
    "DK-2200": {"lat": 55.6888, "lon": 12.5539},  # Nørrebro
    "DK-1600": {"lat": 55.6663, "lon": 12.5458},  # Vesterbro
    "DK-2100": {"lat": 55.7028, "lon": 12.5783},  # Østerbro
    "DK-2300": {"lat": 55.6510, "lon": 12.5850},  # Amager Vest
    "DK-2300-E": {"lat": 55.6580, "lon": 12.6150},# Amager Øst
    "DK-2500": {"lat": 55.6600, "lon": 12.5080},  # Valby
    "DK-2400": {"lat": 55.7080, "lon": 12.5320},  # Bispebjerg
    "DK-2720": {"lat": 55.6880, "lon": 12.4880},  # Vanløse
    "DK-2700": {"lat": 55.7030, "lon": 12.4830},  # Brønshøj-Husum
    "DK-2000": {"lat": 55.6780, "lon": 12.5220}   # Frederiksberg
}

# ---------------------------------------------------------
# Fetch Dati dal Backend FastAPI
# ---------------------------------------------------------
try:
    if total_w == 1.0 and (w_supply != 0.40 or w_demo != 0.35 or w_gap != 0.25):
        # Chiamata alla simulazione What-If
        res = requests.post(
            f"{API_URL}/simulate-cpi",
            json={
                "weight_supply": w_supply,
                "weight_demographics": w_demo,
                "weight_market_gap": w_gap
            }
        )
        sim_data = res.json()["results"]
        
        # Recupera le metriche di base
        base_zones = requests.get(f"{API_URL}/zones").json()
        base_df = pd.DataFrame(base_zones)
        sim_df = pd.DataFrame(sim_data)
        
        df = pd.merge(sim_df, base_df[["district_code", "population_gen_z", "avg_income_dkk", "waste_supply_score", "market_gap_score"]], on="district_code")
        score_col = "simulated_cpi_score"
    else:
        res = requests.get(f"{API_URL}/zones")
        data = res.json()
        df = pd.DataFrame(data)
        score_col = "cpi_score"
        df["rank_change"] = 0

    # Aggiunta coordinate lat/lon al dataframe per la mappa
    df["lat"] = df["district_code"].map(lambda code: DISTRICT_COORDS.get(code, {}).get("lat", 55.6761))
    df["lon"] = df["district_code"].map(lambda code: DISTRICT_COORDS.get(code, {}).get("lon", 12.5683))

    # ---------------------------------------------------------
    # Key Performance Indicators (KPIs)
    # ---------------------------------------------------------
    top_zone = df.iloc[0]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🏆 Top District", top_zone["name"])
    col2.metric("⭐ Highest CPI Score", f"{top_zone[score_col]:.2f}")
    col3.metric("📈 Metro Average CPI", f"{df[score_col].mean():.2f}")
    col4.metric("📍 Zone Analizzate", len(df))

    st.markdown("---")

    # ---------------------------------------------------------
    # Layout a schede (Tabs)
    # ---------------------------------------------------------
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Classifica & Map", 
        "🧩 Breakdown Componenti", 
        "🔍 Scheda Dettaglio Quartiere", 
        "📄 Data Matrix Table"
    ])

    # TAB 1: Classifica e Mappa
    with tab1:
        left_col, right_col = st.columns([1.2, 1])
        
        with left_col:
            st.subheader("Classifica Circular Potential Index")
            fig_bar = px.bar(
                df,
                x="name",
                y=score_col,
                color=score_col,
                labels={"name": "Quartiere", score_col: "CPI Score"},
                color_continuous_scale="Viridis",
                text_auto=".2f"
            )
            fig_bar.update_layout(xaxis_tickangle=-45, showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)

        with right_col:
            st.subheader("Mappa Geografica - Copenhagen & Frederiksberg")
            
            # Supporto compatibile sia per nuove che per vecchie versioni di Plotly
            map_func = getattr(px, "scatter_map", getattr(px, "scatter_mapbox", None))
            style_param = {"map_style": "open-street-map"} if hasattr(px, "scatter_map") else {"mapbox_style": "open-street-map"}
            
            if map_func:
                fig_map = map_func(
                    df,
                    lat="lat",
                    lon="lon",
                    size=score_col,
                    color=score_col,
                    hover_name="name",
                    hover_data={"district_code": True, score_col: ":.2f"},
                    color_continuous_scale="Plasma",
                    size_max=22,
                    zoom=10.5,
                    **style_param
                )
                fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                st.plotly_chart(fig_map, use_container_width=True)
            else:
                st.map(df[["lat", "lon"]])

    # TAB 2: Breakdown dei 3 fattori matematici
    with tab2:
        st.subheader("Composizione del Punteggio CPI per Quartiere")
        st.markdown("Visualizza l'apporto di Rifiuti/Tessile, Demografia Gen Z/Reddito e Vuoto di Mercato sul punteggio finale.")
        
        df["contrib_supply"] = df["waste_supply_score"] * w_supply
        
        def calc_demo_norm(pop, inc):
            g = min(pop / 15000.0, 1.0) * 10.0
            i = min(inc / 450000.0, 1.0) * 10.0
            return (g * 0.6) + (i * 0.4)
            
        df["demo_norm"] = df.apply(lambda r: calc_demo_norm(r["population_gen_z"], r["avg_income_dkk"]), axis=1)
        df["contrib_demo"] = df["demo_norm"] * w_demo
        df["contrib_gap"] = df["market_gap_score"] * w_gap

        fig_stacked = go.Figure(data=[
            go.Bar(name='Supply (Waste)', x=df['name'], y=df['contrib_supply'], marker_color='#2ec4b6'),
            go.Bar(name='Demographics (Gen Z & Income)', x=df['name'], y=df['contrib_demo'], marker_color='#e71d36'),
            go.Bar(name='Market Gap', x=df['name'], y=df['contrib_gap'], marker_color='#ff9f1c')
        ])
        fig_stacked.update_layout(
            barmode='stack',
            title="Scomposizione Punteggio CPI (Attorno ai pesi correnti)",
            xaxis_tickangle=-45,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_stacked, use_container_width=True)

    # TAB 3: Scheda di Dettaglio Singolo Quartiere
    with tab3:
        st.subheader("🔍 Deep-Dive Analitico Quartiere")
        selected_zone_name = st.selectbox("Seleziona una zona metropolitana:", df["name"].unique())
        zone_data = df[df["name"] == selected_zone_name].iloc[0]

        d_col1, d_col2, d_col3, d_col4 = st.columns(4)
        d_col1.metric("Codice Distretto", zone_data["district_code"])
        d_col2.metric("Popolazione Gen Z", f"{int(zone_data['population_gen_z']):,}")
        d_col3.metric("Reddito Medio Annuo", f"{int(zone_data['avg_income_dkk']):,} DKK")
        d_col4.metric("Waste Supply Score", f"{zone_data['waste_supply_score']}/10")

        st.markdown("#### Confronto con le medie di area metropolitana")
        
        metrics_df = pd.DataFrame({
            "Metrica": ["Population Gen Z", "Reddito DKK", "Waste Score", "Market Gap"],
            "Valore Zona": [
                zone_data["population_gen_z"], 
                zone_data["avg_income_dkk"], 
                zone_data["waste_supply_score"], 
                zone_data["market_gap_score"]
            ],
            "Media Metro CPH": [
                df["population_gen_z"].mean(), 
                df["avg_income_dkk"].mean(), 
                df["waste_supply_score"].mean(), 
                df["market_gap_score"].mean()
            ]
        })
        st.dataframe(metrics_df, use_container_width=True)

    # TAB 4: Tabella Dati Operativa & Export
    with tab4:
        st.subheader("Matrice Dati Completa")
        st.dataframe(df.drop(columns=["lat", "lon"], errors="ignore"), use_container_width=True)

        csv_res = requests.get(f"{API_URL}/export/csv")
        if csv_res.status_code == 200:
            st.download_button(
                label="📥 Esporta Report CSV B2B",
                data=csv_res.content,
                file_name="copenhagen_recommerce_matrix.csv",
                mime="text/csv"
            )

except Exception as e:
    st.error(f"Errore di connessione al backend API ({API_URL}). Dettaglio: {str(e)}")