import os
import requests
import streamlit as st
import pandas as pd
import pydeck as pdk
from dotenv import load_dotenv
from cpi_engine import calculate_dynamic_cpi

load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:10000")

# --- CONFIGURAZIONE PAGINA STREAMLIT ---
st.set_page_config(
    page_title="Copenhagen Re-Commerce Matrix | B2B Dashboard",
    page_icon="♻️",
    layout="wide"
)

# --- RECUPERO DATI DISTRETTI ---
@st.cache_data(ttl=60)
def fetch_raw_zones():
    try:
        response = requests.get(f"{API_URL}/zones", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    
    # Fallback dataset se l'API non risponde
    return [
        {"name": "Nørrebro", "lat": 55.6946, "lon": 12.5487, "population_gen_z": 14200, "avg_income_dkk": 310000, "waste_supply_score": 8.5, "demographics_score": 9.0, "market_gap_score": 8.8},
        {"name": "Vesterbro", "lat": 55.6698, "lon": 12.5419, "population_gen_z": 12800, "avg_income_dkk": 340000, "waste_supply_score": 8.0, "demographics_score": 8.5, "market_gap_score": 8.2},
        {"name": "Indre By", "lat": 55.6761, "lon": 12.5683, "population_gen_z": 8500, "avg_income_dkk": 420000, "waste_supply_score": 6.5, "demographics_score": 7.0, "market_gap_score": 6.0},
        {"name": "Østerbro", "lat": 55.7032, "lon": 12.5746, "population_gen_z": 9200, "avg_income_dkk": 390000, "waste_supply_score": 7.0, "demographics_score": 7.5, "market_gap_score": 7.2},
        {"name": "Amager Vest", "lat": 55.6432, "lon": 12.5857, "population_gen_z": 11000, "avg_income_dkk": 350000, "waste_supply_score": 7.5, "demographics_score": 8.0, "market_gap_score": 7.8}
    ]

# --- SIDEBAR: FILTRI DINAMICI B2B ---
st.sidebar.title("♻️ Re-Commerce Matrix")
st.sidebar.markdown("Seleziona il tuo profilo di business per ricalcolare i punteggi CPI dei distretti in tempo reale:")

profile_options = {
    "💼 Boutique / Lusso (Vintage Premium)": "vintage_premium",
    "⚖️ Mercatino a Peso (Kilo Sale)": "kilo_sale",
    "✂️ Laboratorio Sartoriale (Upcycling)": "upcycling",
    "🛍️ Pop-Up di Quartiere (Curated Vintage)": "curated_vintage"
}

selected_label = st.sidebar.selectbox("Modello di Business:", list(profile_options.keys()))
active_profile_key = profile_options[selected_label]

raw_zones = fetch_raw_zones()

# --- CALCOLO DINAMICO CPI ---
processed_zones = []
for zone in raw_zones:
    cpi_res = calculate_dynamic_cpi(zone, business_type=active_profile_key)
    z_data = zone.copy()
    z_data["cpi_score"] = cpi_res["cpi_score"]
    z_data["business_profile_label"] = cpi_res["business_profile_label"]
    processed_zones.append(z_data)

df = pd.DataFrame(processed_zones)
df = df.sort_values(by="cpi_score", ascending=False).reset_index(drop=True)

# --- HEADER PRINCIPALE ---
st.title("♻️ Copenhagen Re-Commerce Matrix")
st.caption(f"Dashboard Executive B2B — Modello Selezionato: {selected_label}")
st.divider()

# --- METRICHE HERO ---
top_zone = df.iloc[0]

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        label="🏆 Distretto Top (CPI)",
        value=top_zone["name"],
        delta=f"{top_zone['cpi_score']:.2f} / 10 CPI"
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

# --- MAPPA 3D & TABELLA CLASSIFICA ---
col_map, col_table = st.columns([1.3, 1])

with col_map:
    st.subheader("📍 Mappa 3D dei Distretti (CPI Dinamico)")
    
    layer = pdk.Layer(
        "ColumnLayer",
        data=df,
        get_position=["lon", "lat"],
        get_elevation="cpi_score * 12000",
        elevation_scale=1,
        radius=800,
        get_fill_color="[110, 142, 128, 210]",
        pickable=True,
        auto_highlight=True,
    )

    view_state = pdk.ViewState(
        latitude=55.6761,
        longitude=12.5683,
        zoom=11.3,
        pitch=45,
        bearing=0
    )

    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "Distretto: {name}\nCPI Score: {cpi_score}\nTarget Gen Z: {population_gen_z}"},
        map_style="mapbox://styles/mapbox/light-v9"
    )

    st.pydeck_chart(r)

with col_table:
    st.subheader("📊 Classifica Distretti (CPI)")
    st.markdown("Graduatoria aggiornata per il profilo di business selezionato.")
    
    display_df = df[["name", "cpi_score", "population_gen_z", "avg_income_dkk"]].copy()
    display_df.columns = ["Distretto", "Indice CPI", "Gen Z Core", "Reddito (DKK)"]
    display_df["Indice CPI"] = display_df["Indice CPI"].round(2)
    display_df["Gen Z Core"] = display_df["Gen Z Core"].map("{:,.0f}".format)
    display_df["Reddito (DKK)"] = display_df["Reddito (DKK)"].map("{:,.0f}".format)
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

st.divider()
st.caption("Copenhagen Re-Commerce Matrix B2B Platform — Streamlit Dashboard")