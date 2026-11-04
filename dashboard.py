import os
import requests
import streamlit as st
import pandas as pd
import pydeck as pdk
from dotenv import load_dotenv
from cpi_engine import calculate_dynamic_cpi

load_dotenv()

# Assicuriamoci che punti al backend Render corretto per scaricare TUTTI i distretti
API_URL = os.getenv("API_URL", "https://copenhagen-recommerce-matrix.onrender.com")

# --- CONFIGURAZIONE PAGINA STREAMLIT ---
st.set_page_config(
    page_title="Copenhagen Re-Commerce Matrix | B2B Dashboard",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STILE CSS DINAMICO (Supporta Tema Chiaro e Scuro) ---
st.markdown("""
    <style>
    /* Usando le variabili di Streamlit, il design si adatta al tema Dark/Light */
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

# --- RECUPERO DATI DISTRETTI ---
@st.cache_data(ttl=60)
def fetch_raw_zones():
    try:
        response = requests.get(f"{API_URL}/zones", timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Errore API: {e}")
    
    return []

# Scala cromatica Verde Salvia 
def assign_sage_color(score: float):
    if score >= 8.5:
        return [62, 89, 79, 255]      # Salvia Scuro (Top)
    elif score >= 7.8:
        return [110, 142, 128, 255]   # Salvia Medio
    elif score >= 7.0:
        return [153, 179, 168, 255]   # Salvia Chiaro
    else:
        return [200, 215, 209, 200]   # Salvia Sbiadito

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

# --- CALCOLO DINAMICO CPI & COLORE ---
processed_zones = []
for zone in raw_zones:
    cpi_res = calculate_dynamic_cpi(zone, business_type=active_profile_key)
    z_data = zone.copy()
    c_score = cpi_res["cpi_score"]
    z_data["cpi_score"] = c_score
    z_data["business_profile_label"] = cpi_res["business_profile_label"]
    
    # Esageriamo l'altezza per rendere la mappa più leggibile e applichiamo il colore salvia
    z_data["elevation"] = max((c_score - 4.0), 0.5) * 450
    z_data["color"] = assign_sage_color(c_score)
    
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

    # --- MAPPA 3D & TABELLA CLASSIFICA ---
    col_map, col_table = st.columns([1.3, 1])

    with col_map:
        st.subheader("📍 Mappa 3D dei Distretti")
        
        layer = pdk.Layer(
            "ColumnLayer",
            data=df,
            get_position=["lon", "lat"],
            get_elevation="elevation",
            elevation_scale=1,
            radius=350,
            get_fill_color="color",
            pickable=True,
            auto_highlight=True,
        )

        view_state = pdk.ViewState(
            latitude=55.6800,
            longitude=12.5600,
            zoom=11.3,
            pitch=45,
            bearing=-15
        )

        r = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={"text": "Distretto: {name}\nCPI Score: {cpi_score}\nTarget Gen Z: {population_gen_z}"},
            map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
        )

        st.pydeck_chart(r)

    with col_table:
        st.subheader("📊 Classifica Completa (CPI)")
        
        display_df = df[["name", "cpi_score", "population_gen_z", "avg_income_dkk"]].copy()
        display_df.columns = ["Distretto", "Indice CPI", "Gen Z Core", "Reddito (DKK)"]
        display_df["Indice CPI"] = display_df["Indice CPI"].round(2)
        display_df["Gen Z Core"] = display_df["Gen Z Core"].map("{:,.0f}".format)
        display_df["Reddito (DKK)"] = display_df["Reddito (DKK)"].map("{:,.0f}".format)
        
        st.dataframe(display_df, height=450, use_container_width=True, hide_index=True)

else:
    st.error("⚠️ Nessun distretto recuperato dal database. In attesa del caricamento API da Render...")

st.divider()
st.caption("Copenhagen Re-Commerce Matrix B2B Platform — Streamlit Dashboard")