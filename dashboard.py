import os
import requests
import streamlit as st
import pandas as pd
import pydeck as pdk
from dotenv import load_dotenv
from cpi_engine import calculate_dynamic_cpi

load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:10000")

# --- CONFIGURAZIONE PAGINA STREAMLIT (Tema Executive) ---
st.set_page_config(
    page_title="Copenhagen Re-Commerce Matrix | B2B Dashboard",
    page_icon="♻️",
    layout="wide"
)

# --- STYLING & CSS PERSONALIZZATO ---
st.markdown("""
    <style>
    .main {
        background-color: #FAFAFA;
    }
    .metric-card {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        border-left: 4px solid #6E8E80;
    }
    </style>
""", unsafe_allow_html=True)

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
st.markdown(f"**Dashboard Executive B2B** — Modello Selezionato: *{selected_label}*")
st.markdown("---")

# --- METRICHE HERO (Top 3 Indicatori) ---
top_zone = df.iloc[0]

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
        <div class="metric-card">
            <h4>🏆 Distretto Top (CPI)</h4>
            <h2>{top_zone['name']}</h2>
            <p style="color: #6E8E80; font-weight: bold;">Punteggio: {top_zone['cpi_score']:.2f} / 10</p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class