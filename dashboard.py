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

# --- CSS EXECUTIVE ---
st.markdown("""
    <style>
    /* Card delle Metriche */
    div[data-testid="stMetric"] {
        background-color: var(--secondary-background-color);
        border-left: 4px solid #7EAA96;
        border-top: 1px solid var(--border-color);
        border-right: 1px solid var(--border-color);
        border-bottom: 1px solid var(--border-color);
        padding: 20px;
        border-radius: 16px !important;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
    }
    /* Contenitori mappa e tabella stondati */
    [data-testid="stDeckGlJsonChart"], [data-testid="stDataFrame"] {
        border-radius: 16px !important;
        overflow: hidden !important;
        border: 1px solid var(--border-color);
    }
    hr {
        border-color: #7EAA96;
        opacity: 0.2;
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

# --- GRADIENTE VERDE SALVIA (Ottimizzato per mappa scura) ---
def get_sage_gradient(score: float):
    if score >= 8.5:
        return [100, 220, 160, 240]   # Verde Menta/Salvia Luminoso (Top)
    elif score >= 7.5:
        return [80, 170, 130, 210]    # Salvia Scuro
    elif score >= 6.5:
        return [60, 120, 100, 180]    # Salvia Spento
    else:
        return [40, 70, 60, 120]      # Verde scurissimo, quasi trasparente (Basso)

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
    
    # Chiave per il match (tutto minuscolo)
    norm_name = z_data["name"].lower().strip()
    zone_data_map[norm_name] = z_data

df = pd.DataFrame(processed_zones)
df = df.sort_values(by="cpi_score", ascending=False).reset_index(drop=True)

# --- MERGE INTO GEOJSON (Con Match Intelligente dei nomi) ---
if geojson_data:
    for feature in geojson_data["features"]:
        geo_name = feature["properties"]["name"].lower().strip()
        
        # Trova una corrispondenza parziale tra i nomi (es. "Vesterbro" in "Vesterbro / Kongens...")
        matched_score = 0
        matched_gen_z = 0
        
        for api_name, z_info in zone_data_map.items():
            if geo_name in api_name or api_name in geo_name:
                matched_score = z_info["cpi_score"]
                matched_gen_z = z_info["population_gen_z"]
                break
        
        feature["properties"]["cpi_score"] = matched_score
        feature["properties"]["gen_z"] = matched_gen_z
        
        # Altezze enfatizzate e colore
        if matched_score > 0:
            feature["properties"]["elevation"] = max((matched_score - 4.5), 0.1) * 1200 
            feature["properties"]["fill_color"] = get_sage_gradient(matched_score)
        else:
            feature["properties"]["elevation"] = 0
            feature["properties"]["fill_color"] = [30, 30, 30, 100] # Grigio scuro per zone senza dati

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
        st.subheader("📍 Topografia del Valore B2B")
        
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
                get_line_color=[255, 255, 255, 50],
                pickable=True,
                auto_highlight=True,
            )

            view_state = pdk.ViewState(
                latitude=55.67,
                longitude=12.55,
                zoom=10.5, 
                pitch=55, # Più inclinato per far risaltare il 3D
                bearing=-10
            )

            r = pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                tooltip={
                    "html": "<b>{name}</b><br/>CPI Score: {cpi_score}<br/>Gen Z: {gen_z}",
                    "style": {"backgroundColor": "#1E293B", "color": "white", "borderRadius": "8px"}
                },
                # Mappa di base scura per far brillare il verde salvia
                map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json" 
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
        
        # Rimossa l'altezza fissa: ora la tabella abbraccia perfettamente il numero di righe senza spazi neri vuoti
        st.dataframe(display_df, use_container_width=True, hide_index=True)

else:
    st.error("⚠️ Nessun distretto recuperato dal database.")

st.divider()
st.caption("Copenhagen Re-Commerce Matrix B2B Platform — Streamlit Dashboard")