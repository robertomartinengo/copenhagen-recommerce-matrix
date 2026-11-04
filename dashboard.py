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

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Copenhagen Re-Commerce Matrix | B2B Dashboard",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS EXECUTIVE (Angoli stondati e stile pulito) ---
st.markdown("""
    <style>
    /* Card delle Metriche: Stondate e con bordo tenue */
    div[data-testid="stMetric"] {
        background-color: var(--secondary-background-color);
        border: 1px solid #D1DCD7;
        padding: 20px;
        border-radius: 16px !important;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.03);
    }
    /* Contenitore Mappa PyDeck: Stondato */
    [data-testid="stDeckGlJsonChart"] {
        border-radius: 16px !important;
        overflow: hidden !important;
        border: 1px solid #D1DCD7;
    }
    /* Contenitore Tabella: Stondato */
    [data-testid="stDataFrame"] {
        border-radius: 16px !important;
        overflow: hidden !important;
        border: 1px solid #D1DCD7;
    }
    hr {
        border-color: #6E8E80;
        opacity: 0.15;
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
    except Exception:
        return None

# --- GRADIENTE VERDE SALVIA EXECUTIVE ---
def get_sage_gradient(score: float):
    if score >= 8.5:
        return [62, 89, 79, 230]      # Salvia Scuro / Intenso (Top CPI)
    elif score >= 7.5:
        return [110, 142, 128, 210]   # Salvia Medio
    elif score >= 6.5:
        return [170, 189, 180, 190]   # Salvia Chiaro
    else:
        return [235, 240, 238, 170]   # Quasi Bianco / Salvia Sbiadito (Low CPI)

# --- SIDEBAR: FILTRI DINAMICI ---
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

# --- CALCOLO CPI DINAMICO ---
processed_zones = []
zone_data_map = {} 

for zone in raw_zones:
    cpi_res = calculate_dynamic_cpi(zone, business_type=active_profile_key)
    z_data = zone.copy()
    score = cpi_res["cpi_score"]
    z_data["cpi_score"] = score
    z_data["business_profile_label"] = cpi_res["business_profile_label"]
    processed_zones.append(z_data)
    
    norm_name = z_data["name"].lower().strip()
    zone_data_map[norm_name] = z_data

df = pd.DataFrame(processed_zones)
df = df.sort_values(by="cpi_score", ascending=False).reset_index(drop=True)

# --- MERGE DATI CON GEOJSON PER LA MAPPA ---
if geojson_data:
    for feature in geojson_data["features"]:
        dist_name = feature["properties"]["name"].lower().strip()
        if dist_name in zone_data_map:
            z_info = zone_data_map[dist_name]
            score = z_info["cpi_score"]
            feature["properties"]["cpi_score"] = score
            feature["properties"]["gen_z"] = z_info["population_gen_z"]
            
            # Altezza elegante (più schiacciata) e colore gradiente salvia
            feature["properties"]["elevation"] = max((score - 5.0), 0) * 250 
            feature["properties"]["fill_color"] = get_sage_gradient(score)
        else:
            feature["properties"]["cpi_score"] = 0
            feature["properties"]["gen_z"] = 0
            feature["properties"]["elevation"] = 0
            feature["properties"]["fill_color"] = [240, 240, 240, 100]

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

    # --- MAPPA 3D E TABELLA ---
    col_map, col_table = st.columns([1.5, 1])

    with col_map:
        st.subheader("📍 Mappa di Calore 3D")
        
        if geojson_data:
            layer = pdk.Layer(
                "GeoJsonLayer",
                geojson_data,
                opacity=0.9,
                stroked=True,
                filled=True,
                extruded=True,
                wireframe=True,
                get_elevation="properties.elevation",
                get_fill_color="properties.fill_color",
                get_line_color=[255, 255, 255, 180], # Bordi bianchi leggeri tra distretti
                pickable=True,
                auto_highlight=True,
            )

            # Inquadratura più ampia e meno inclinata
            view_state = pdk.ViewState(
                latitude=55.67,
                longitude=12.55,
                zoom=10.2, 
                pitch=40,
                bearing=0
            )

            r = pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                tooltip={
                    "html": "<b>{name}</b><br/>CPI Score: {cpi_score}<br/>Gen Z: {gen_z}",
                    "style": {"backgroundColor": "#2F3E37", "color": "white", "borderRadius": "8px"}
                },
                map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
            )

            st.pydeck_chart(r)
        else:
            st.error("File GeoJSON non trovato.")

    with col_table:
        st.subheader("📊 Classifica Distretti")
        
        display_df = df[["name", "cpi_score", "population_gen_z", "avg_income_dkk"]].copy()
        display_df.columns = ["Distretto", "Indice CPI", "Gen Z Core", "Reddito (DKK)"]
        display_df["Indice CPI"] = display_df["Indice CPI"].round(2)
        display_df["Gen Z Core"] = display_df["Gen Z Core"].map("{:,.0f}".format)
        display_df["Reddito (DKK)"] = display_df["Reddito (DKK)"].map("{:,.0f}".format)
        
        st.dataframe(display_df, height=450, use_container_width=True, hide_index=True)

else:
    st.error("⚠️ Nessun distretto recuperato dal database.")

st.divider()
st.caption("Copenhagen Re-Commerce Matrix B2B Platform — Streamlit Dashboard")