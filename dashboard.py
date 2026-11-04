import os
import requests
import json
import streamlit as st
import pandas as pd
import pydeck as pdk
from dotenv import load_dotenv
from cpi_engine import calculate_dynamic_cpi

load_dotenv()

API_URL = os.getenv("API_URL", "https://copenhagen-recommerce-matrix.onrender.com")

# --- CONFIGURAZIONE PAGINA STREAMLIT ---
st.set_page_config(
    page_title="Copenhagen Re-Commerce Matrix | B2B Dashboard",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STILE CSS DINAMICO ---
st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: var(--secondary-background-color);
        border-left: 5px solid #6E8E80;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.05);
    }
    hr {
        border-color: #6E8E80;
        opacity: 0.3;
    }
    </style>
""", unsafe_allow_html=True)

# --- RECUPERO DATI E GEOJSON ---
@st.cache_data(ttl=60)
def fetch_raw_zones():
    try:
        response = requests.get(f"{API_URL}/zones", timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Errore API: {e}")
    return []

@st.cache_data
def load_geojson():
    try:
        with open("copenhagen_districts.geojson", "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Errore GeoJSON: {e}")
        return None

# Scala cromatica (dal verde intenso per score alti a rosso scuro per score bassi)
def get_fill_color(score: float):
    if score >= 8.5:
        return [34, 197, 94, 200]    # Verde Brillante (Top)
    elif score >= 7.5:
        return [110, 142, 128, 200]  # Verde Salvia 
    elif score >= 6.5:
        return [234, 179, 8, 200]    # Giallo
    else:
        return [239, 68, 68, 200]    # Rosso (Basso potenziale)

# --- SIDEBAR: FILTRI DINAMICI B2B ---
st.sidebar.title("♻️ Re-Commerce Matrix")
st.sidebar.markdown("Seleziona il profilo di business per ricalcolare i punteggi CPI in tempo reale:")

profile_options = {
    "💼 Boutique / Lusso (Vintage Premium)": "vintage_premium",
    "⚖️ Mercatino a Peso (Kilo Sale)": "kilo_sale",
    "✂️ Laboratorio Sartoriale (Upcycling)": "upcycling",
    "🛍️ Pop-Up di Quartiere (Curated Vintage)": "curated_vintage"
}

selected_label = st.sidebar.selectbox("Modello di Business:", list(profile_options.keys()))
active_profile_key = profile_options[selected_label]

raw_zones = fetch_raw_zones()
geojson_data = load_geojson()

# --- CALCOLO DINAMICO CPI & MERGE CON GEOJSON ---
processed_zones = []
zone_data_map = {} # Per unire i dati facilmente con il geojson

for zone in raw_zones:
    cpi_res = calculate_dynamic_cpi(zone, business_type=active_profile_key)
    z_data = zone.copy()
    c_score = cpi_res["cpi_score"]
    z_data["cpi_score"] = c_score
    z_data["business_profile_label"] = cpi_res["business_profile_label"]
    processed_zones.append(z_data)
    
    # Rendi la chiave del distretto compatibile (minuscolo, senza spazi strani)
    norm_name = z_data["name"].lower().strip()
    zone_data_map[norm_name] = z_data

df = pd.DataFrame(processed_zones)
df = df.sort_values(by="cpi_score", ascending=False).reset_index(drop=True)

# Se abbiamo il geojson, iniettiamo score, colore e altezza nelle properties
if geojson_data:
    for feature in geojson_data["features"]:
        dist_name = feature["properties"]["name"].lower().strip()
        if dist_name in zone_data_map:
            z_info = zone_data_map[dist_name]
            score = z_info["cpi_score"]
            feature["properties"]["cpi_score"] = score
            feature["properties"]["gen_z"] = z_info["population_gen_z"]
            
            # Calcolo elevazione (altezza in metri basata sul CPI) e colore
            feature["properties"]["elevation"] = max((score - 4.0), 0) * 1500
            feature["properties"]["fill_color"] = get_fill_color(score)
        else:
            # Distretti non nel DB
            feature["properties"]["cpi_score"] = 0
            feature["properties"]["gen_z"] = 0
            feature["properties"]["elevation"] = 0
            feature["properties"]["fill_color"] = [200, 200, 200, 50] # Grigio semitrasparente


# --- HEADER PRINCIPALE ---
st.title("♻️ Copenhagen Re-Commerce Matrix")
st.caption(f"**Dashboard Executive B2B** — Analisi per: {selected_label}")
st.divider()

if not df.empty:
    # --- METRICHE HERO ---
    top_zone = df.iloc[0]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="🏆 Distretto Top (CPI)",
            value=top_zone["name"],
            delta=f"{top_zone['cpi_score']:.2f} / 10"
        )
    with col2:
        st.metric(
            label="👥 Target Gen Z Core",
            value=f"{top_zone['population_gen_z']:,.0f}",
            delta=f"Residenti a {top_zone['name']}"
        )
    with col3:
        st.metric(
            label="💰 Reddito Medio Pro-Capite",
            value=f"{top_zone['avg_income_dkk']:,.0f} DKK",
            delta="Annuo"
        )

    st.write("")

    # --- MAPPA 3D (GEOJSON) & TABELLA CLASSIFICA ---
    col_map, col_table = st.columns([1.5, 1])

    with col_map:
        st.subheader("📍 Mappa di Calore 3D dei Distretti (CPI)")
        
        if geojson_data:
            # Layer GeoJson 3D
            layer = pdk.Layer(
                "GeoJsonLayer",
                geojson_data,
                opacity=0.8,
                stroked=True,
                filled=True,
                extruded=True,
                wireframe=True,
                get_elevation="properties.elevation",
                get_fill_color="properties.fill_color",
                get_line_color=[255, 255, 255],
                pickable=True,
                auto_highlight=True,
            )

            view_state = pdk.ViewState(
                latitude=55.6761,
                longitude=12.5683,
                zoom=10.5,
                pitch=55,
                bearing=-15
            )

            r = pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                tooltip={
                    "html": "<b>Distretto:</b> {name}<br/><b>CPI Score:</b> {cpi_score}<br/><b>Gen Z:</b> {gen_z}",
                    "style": {"backgroundColor": "steelblue", "color": "white"}
                },
                map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
            )

            st.pydeck_chart(r)
        else:
            st.error("File GeoJSON non trovato. Impossibile renderizzare la mappa.")

    with col_table:
        st.subheader("📊 Classifica Completa (CPI)")
        
        display_df = df[["name", "cpi_score", "population_gen_z", "avg_income_dkk"]].copy()
        display_df.columns = ["Distretto", "Indice CPI", "Gen Z Core", "Reddito (DKK)"]
        display_df["Indice CPI"] = display_df["Indice CPI"].round(2)
        display_df["Gen Z Core"] = display_df["Gen Z Core"].map("{:,.0f}".format)
        display_df["Reddito (DKK)"] = display_df["Reddito (DKK)"].map("{:,.0f}".format)
        
        st.dataframe(display_df, height=500, use_container_width=True, hide_index=True)

else:
    st.error("⚠️ Nessun distretto recuperato dal database.")

st.divider()
st.caption("Copenhagen Re-Commerce Matrix B2B Platform — Streamlit Dashboard")