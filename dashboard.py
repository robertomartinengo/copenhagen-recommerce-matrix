import os
import requests
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

# --- CSS EXECUTIVE (Stondato e Adattivo) ---
st.markdown("""
    <style>
    /* Stondatura globale per tutti i contenitori */
    div[data-testid="stMetric"], 
    [data-testid="stDeckGlJsonChart"], 
    [data-testid="stDataFrame"] {
        border-radius: 16px !important;
        overflow: hidden !important;
    }
    
    /* Dettaglio Salvia sulle metriche (adattivo a Light/Dark) */
    div[data-testid="stMetric"] {
        border-top: 4px solid #7EAA96;
        background-color: var(--secondary-background-color);
        padding: 15px 20px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.05);
    }
    hr {
        border-color: #7EAA96;
        opacity: 0.2;
    }
    </style>
""", unsafe_allow_html=True)

# --- RECUPERO DATI API ---
@st.cache_data(ttl=60)
def fetch_raw_zones():
    try:
        response = requests.get(f"{API_URL}/zones", timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Errore API: {e}")
    return []

# --- GRADIENTE DA BIANCO/GRIGIO A VERDE SALVIA ---
def get_sage_gradient(score: float):
    # La mappa va da bianco latte/grigio chiaro (score bassi) a Salvia scuro (score alti)
    if score >= 8.5:
        return [70, 115, 95, 240]     # Verde Salvia Scuro / Intenso
    elif score >= 7.5:
        return [110, 150, 130, 220]   # Verde Salvia Medio
    elif score >= 6.5:
        return [160, 185, 175, 200]   # Verde Salvia Chiaro
    elif score >= 5.5:
        return [210, 220, 215, 180]   # Grigio/Verdino chiarissimo
    else:
        return [245, 245, 245, 150]   # Bianco/Grigio neutro (Quasi trasparente)

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

# --- CALCOLO CPI DINAMICO ---
processed_zones = []
for zone in raw_zones:
    cpi_res = calculate_dynamic_cpi(zone, business_type=active_profile_key)
    z_data = zone.copy()
    score = cpi_res["cpi_score"]
    z_data["cpi_score"] = score
    z_data["business_profile_label"] = cpi_res["business_profile_label"]
    
    # Moltiplicatore altezza per rendere le differenze nette, partendo da una base minima
    z_data["elevation"] = max((score - 4.5), 0.5) * 800 
    z_data["color"] = get_sage_gradient(score)
    
    # Coordinate fisse centrali per distretti problematici
    if "Vesterbro" in z_data["name"]:
        z_data["lat"], z_data["lon"] = 55.66, 12.53
    elif "Bispebjerg" in z_data["name"]:
        z_data["lat"], z_data["lon"] = 55.71, 12.53

    processed_zones.append(z_data)

df = pd.DataFrame(processed_zones)
df = df.sort_values(by="cpi_score", ascending=False).reset_index(drop=True)

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
        
        # Sfondo della mappa basato sul tema di Streamlit 
        # (Se l'utente ha il tema scuro, usa Dark Matter, altrimenti usa Positron chiaro)
        theme_map_style = "mapbox://styles/mapbox/dark-v10" if st.get_option("theme.base") == "dark" else "mapbox://styles/mapbox/light-v10"
        
        # Layer a Cilindri (ColumnLayer) per evitare blocchi spigolosi
        layer = pdk.Layer(
            "ColumnLayer",
            data=df,
            get_position=["lon", "lat"],
            get_elevation="elevation",
            elevation_scale=1,
            radius=450, # Raggio fisso e pulito
            disk_resolution=30, # Rende i cilindri perfettamente tondi
            get_fill_color="color",
            pickable=True,
            auto_highlight=True,
        )

        view_state = pdk.ViewState(
            latitude=55.675,
            longitude=12.56,
            zoom=10.5, 
            pitch=50, 
            bearing=-15
        )

        r = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={
                "html": "<b>{name}</b><br/>CPI Score: {cpi_score}<br/>Gen Z: {population_gen_z}",
                "style": {"backgroundColor": "#2F3E37", "color": "white", "borderRadius": "8px"}
            },
            # Mapbox base (Molto più elegante di Carto)
            map_style=theme_map_style
        )

        st.pydeck_chart(r)

    with col_table:
        st.subheader("📊 Classifica Distretti")
        
        display_df = df[["name", "cpi_score", "population_gen_z", "avg_income_dkk"]].copy()
        display_df.columns = ["Distretto", "Indice CPI", "Gen Z Core", "Reddito (DKK)"]
        display_df["Indice CPI"] = display_df["Indice CPI"].round(2)
        display_df["Gen Z Core"] = display_df["Gen Z Core"].map("{:,.0f}".format)
        display_df["Reddito (DKK)"] = display_df["Reddito (DKK)"].map("{:,.0f}".format)
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)

else:
    st.error("⚠️ Nessun distretto recuperato dal database. Verifica l'API.")

st.divider()
st.caption("Copenhagen Re-Commerce Matrix B2B Platform — Streamlit Dashboard")