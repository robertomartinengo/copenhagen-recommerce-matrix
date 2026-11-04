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

# --- CSS EXECUTIVE (Stondatura Universale) ---
st.markdown("""
    <style>
    /* Card, Mappa e Tabella totalmente stondate */
    div[data-testid="stMetric"], 
    div[data-testid="stDeckGlJsonChart"], 
    div[data-testid="stDataFrame"] {
        border-radius: 16px !important;
        overflow: hidden !important;
    }
    
    div[data-testid="stMetric"] {
        border-top: 5px solid #6E8E80;
        background-color: var(--secondary-background-color);
        padding: 15px 20px;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.04);
        border-bottom: 1px solid var(--border-color);
        border-left: 1px solid var(--border-color);
        border-right: 1px solid var(--border-color);
    }
    hr { border-color: #6E8E80; opacity: 0.2; }
    </style>
""", unsafe_allow_html=True)

# --- COORDINATE DI BACKUP (Risolve il problema delle colonne mancanti) ---
COPENHAGEN_COORDS = {
    "nørrebro": (55.6946, 12.5487),
    "vesterbro / kongens enghave": (55.6600, 12.5300),
    "vesterbro": (55.6698, 12.5419),
    "indre by": (55.6761, 12.5683),
    "østerbro": (55.7032, 12.5746),
    "amager vest": (55.6432, 12.5857),
    "amager øst": (55.6632, 12.6157),
    "bispebjerg": (55.7100, 12.5300),
    "valby": (55.6600, 12.5000),
    "frederiksberg": (55.6794, 12.5346),
    "vanløse": (55.6872, 12.4933),
    "brønshøj-husum": (55.7100, 12.4800)
}

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

# --- GRADIENTE SALVIA (Dal chiaro allo scuro) ---
def get_sage_gradient(score: float):
    if score >= 8.2:
        return [47, 79, 79, 255]      # Verde Salvia Scuro / Intenso
    elif score >= 7.4:
        return [110, 142, 128, 255]   # Verde Salvia Medio
    elif score >= 6.6:
        return [165, 190, 175, 255]   # Verde Salvia Chiaro
    elif score >= 6.0:
        return [210, 225, 215, 255]   # Grigio-Verdino Sbiadito
    else:
        return [245, 248, 246, 255]   # Bianco Latte / Quasi Trasparente

# --- SIDEBAR: FILTRI DINAMICI ---
st.sidebar.title("♻️ Re-Commerce Matrix")
st.sidebar.markdown("Seleziona il profilo per ricalcolare il potenziale:")

profile_options = {
    "💼 Boutique / Lusso (Vintage Premium)": "vintage_premium",
    "⚖️ Mercatino a Peso (Kilo Sale)": "kilo_sale",
    "✂️ Laboratorio Sartoriale (Upcycling)": "upcycling",
    "🛍️ Pop-Up di Quartiere (Curated Vintage)": "curated_vintage"
}

selected_label = st.sidebar.selectbox("Modello di Business:", list(profile_options.keys()))
active_profile_key = profile_options[selected_label]

raw_zones = fetch_raw_zones()

# --- ELABORAZIONE DATI ---
processed_zones = []
for zone in raw_zones:
    cpi_res = calculate_dynamic_cpi(zone, business_type=active_profile_key)
    z_data = zone.copy()
    score = cpi_res["cpi_score"]
    z_data["cpi_score"] = score
    
    # Iniezione forzata delle coordinate se mancano nel DB
    name_lower = z_data["name"].lower().strip()
    if name_lower in COPENHAGEN_COORDS:
        z_data["lat"] = COPENHAGEN_COORDS[name_lower][0]
        z_data["lon"] = COPENHAGEN_COORDS[name_lower][1]
    
    # Se per qualche motivo lat e lon sono assenti o a zero, saltiamo
    if z_data.get("lat", 0) == 0:
        continue

    # Altezza esagerata in base al punteggio per distacco visivo
    z_data["elevation"] = max((score - 4.5), 0.5) * 800 
    z_data["fill_color"] = get_sage_gradient(score)
    processed_zones.append(z_data)

df = pd.DataFrame(processed_zones)
if not df.empty:
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
        
        # Livello a colonne cilindriche (rotonde e lisce)
        layer = pdk.Layer(
            "ColumnLayer",
            data=df,
            get_position=["lon", "lat"],
            get_elevation="elevation",
            elevation_scale=1,
            radius=400,          # Raggio proporzionato
            disk_resolution=40,  # Alta risoluzione = cilindri perfettamente rotondi
            get_fill_color="fill_color",
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

        # Rimosso il map_style fisso. 
        # Lasciandolo a "None" permettiamo a Streamlit di iniettare il suo tema!
        r = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={
                "html": "<b>{name}</b><br/>CPI Score: {cpi_score}<br/>Gen Z: {population_gen_z}",
                "style": {"backgroundColor": "#6E8E80", "color": "white", "borderRadius": "8px"}
            },
            map_style=None
        )

        # Il parametro theme="streamlit" sincronizza magicamente la mappa con il tema Light/Dark
        st.pydeck_chart(r, theme="streamlit")

    with col_table:
        st.subheader("📊 Classifica Distretti")
        
        display_df = df[["name", "cpi_score", "population_gen_z", "avg_income_dkk"]].copy()
        display_df.columns = ["Distretto", "Indice CPI", "Gen Z Core", "Reddito (DKK)"]
        display_df["Indice CPI"] = display_df["Indice CPI"].round(2)
        display_df["Gen Z Core"] = display_df["Gen Z Core"].map("{:,.0f}".format)
        display_df["Reddito (DKK)"] = display_df["Reddito (DKK)"].map("{:,.0f}".format)
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)

else:
    st.error("⚠️ Nessun distretto elaborato. Verifica la connessione API.")

st.divider()
st.caption("Copenhagen Re-Commerce Matrix B2B Platform — Streamlit Dashboard")