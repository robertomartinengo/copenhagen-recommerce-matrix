import os
import pandas as pd
import streamlit as st
import pydeck as pdk
import plotly.express as px
import requests
from pdf_generator import generate_executive_pdf

# 1. Configurazione Pagina
st.set_page_config(
    page_title="Copenhagen Re-Commerce Matrix",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = "https://copenhagen-recommerce-matrix.onrender.com"

# 2. Custom CSS (Rimosso lo sfondo fisso, mantenuto solo lo stile per bottoni e KPI)
st.markdown("""
    <style>
    /* Metric Cards */
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
        color: #6E8E80 !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
    }
    /* Buttons */
    .stButton>button {
        background-color: #6E8E80;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 8px 16px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #587367;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)


# 3. Caricamento Dati
@st.cache_data(ttl=60)
def load_zones_data():
    try:
        response = requests.get(f"{API_URL}/zones", timeout=15.0)
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            for col in ["cpi_score", "waste_supply_score", "demographics_score", "market_gap_score"]:
                if col in df.columns:
                    df[col] = df[col].astype(float)
            return df
    except Exception as e:
        st.sidebar.warning(f"⚠️ Impossibile connettersi all'API. Uso dati locali. ({e})")
    
    # Fallback
    fallback = [
        {"name": "Nørrebro", "cpi_score": 8.89, "population_gen_z": 14200, "avg_income_dkk": 290000},
        {"name": "Vesterbro / Kongens Enghave", "cpi_score": 7.58, "population_gen_z": 9800, "avg_income_dkk": 340000},
    ]
    return pd.DataFrame(fallback)

df = load_zones_data()

# Coordinate geografiche
DISTRICT_COORDS = {
    "Indre By": {"lat": 55.6800, "lon": 12.5800},
    "Nørrebro": {"lat": 55.6888, "lon": 12.5562},
    "Vesterbro / Kongens Enghave": {"lat": 55.6667, "lon": 12.5450},
    "Østerbro": {"lat": 55.7000, "lon": 12.5700},
    "Amager Vest": {"lat": 55.6400, "lon": 12.5800},
    "Amager Øst": {"lat": 55.6550, "lon": 12.6100},
    "Valby": {"lat": 55.6580, "lon": 12.5150},
    "Bispebjerg": {"lat": 55.7150, "lon": 12.5300},
    "Vanløse": {"lat": 55.6880, "lon": 12.4880},
    "Brønshøj-Husum": {"lat": 55.7050, "lon": 12.4850},
    "Frederiksberg": {"lat": 55.6780, "lon": 12.5320}
}

if "lat" not in df.columns or "lon" not in df.columns:
    df["lat"] = df["name"].map(lambda x: DISTRICT_COORDS.get(x, {}).get("lat", 55.6761))
    df["lon"] = df["name"].map(lambda x: DISTRICT_COORDS.get(x, {}).get("lon", 12.5683))

# --- SIDEBAR ---
st.sidebar.image("https://img.icons8.com/isometric/100/recycle.png", width=60)
st.sidebar.title("Filtri Strategici")

min_cpi = st.sidebar.slider("Punteggio CPI Minimo", 0.0, 10.0, 5.0, 0.1)
min_genz = st.sidebar.number_input("Popolazione Gen Z Minima", 0, 30000, 0, 1000)

filtered_df = df[(df["cpi_score"] >= min_cpi) & (df["population_gen_z"] >= min_genz)].sort_values(by="cpi_score", ascending=False).copy()

# --- KPI HEADER ---
st.title("♻️ Copenhagen Re-Commerce Matrix")
st.subheader("Executive Market Intelligence Dashboard")

col1, col2, col3, col4 = st.columns(4)
top_zone = filtered_df.iloc[0] if len(filtered_df) > 0 else None

col1.metric("Distretti Analizzati", f"{len(filtered_df)} / {len(df)}")
col2.metric("Top Location CPI", top_zone["name"] if top_zone is not None else "N/A", f"CPI {top_zone['cpi_score']:.1f}" if top_zone is not None else None)
col3.metric("Target Gen Z", f"{filtered_df['population_gen_z'].sum():,.0f}" if len(filtered_df) > 0 else 0)
col4.metric("Media CPI", f"{filtered_df['cpi_score'].mean():.2f} / 10" if len(filtered_df) > 0 else "0.00")
st.markdown("---")

# --- CONTENUTO PRINCIPALE ---
col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown("### 🗺️ Mappa Spaziale (Pydeck 3D)")
    
    if len(filtered_df) > 0:
        # Dinamicità Mappa: Calcolo altezza esponenziale e colore sfumato
        min_score = filtered_df["cpi_score"].min()
        max_score = filtered_df["cpi_score"].max()
        score_range = max_score - min_score if max_score != min_score else 1

        def get_color(cpi):
            norm = (cpi - min_score) / score_range
            # Sfuma dal Grigio Chiaro [200,200,200] al Verde Salvia [110, 142, 128]
            r = int(200 - (200 - 110) * norm)
            g = int(200 - (200 - 142) * norm)
            b = int(200 - (200 - 128) * norm)
            return [r, g, b, 230]

        filtered_df["color"] = filtered_df["cpi_score"].apply(get_color)
        # Curva esponenziale per far saltare all'occhio i punteggi più alti
        filtered_df["elevation"] = (filtered_df["cpi_score"] ** 3) * 3 

        layer = pdk.Layer(
            "ColumnLayer",
            data=filtered_df,
            get_position=["lon", "lat"],
            get_elevation="elevation",
            elevation_scale=1,
            radius=400,
            get_fill_color="color",
            pickable=True,
            auto_highlight=True,
        )
        
        view_state = pdk.ViewState(latitude=55.6761, longitude=12.5683, zoom=10.5, pitch=50, bearing=0)
        
        r = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={"text": "{name}\nCPI: {cpi_score}\nGen Z: {population_gen_z}"}
        )
        st.pydeck_chart(r)

with col_right:
    st.markdown("### 🏆 Classifica CPI")
    if len(filtered_df) > 0:
        fig = px.bar(
            filtered_df, x="cpi_score", y="name", orientation="h",
            color="cpi_score", color_continuous_scale=["#EBF0ED", "#6E8E80"],
            text_auto=".1f"
        )
        # theme="streamlit" risolve il problema dei colori del testo sovrascritti
        fig.update_layout(
            yaxis={"categoryorder": "total ascending"},
            showlegend=False,
            height=400,
            margin=dict(l=0, r=0, t=10, b=10)
        )
        st.plotly_chart(fig, use_container_width=True, theme="streamlit")

# --- GENERATORE PDF ---
st.markdown("---")
st.markdown("### 📄 Generatore Report Executive PDF B2B")
col_sel, col_btn = st.columns([3, 1])

with col_sel:
    selected_district = st.selectbox("Seleziona un distretto:", df["name"].tolist())

with col_btn:
    st.write(""); st.write("")
    if st.button("📥 Genera PDF"):
        zone_data = df[df["name"] == selected_district].iloc[0].to_dict()
        filename = f"Executive_Report_{selected_district.replace(' ', '_')}.pdf"
        generate_executive_pdf(zone_data, filename=filename)
        with open(filename, "rb") as file:
            st.download_button("⬇️ Scarica Ora", data=file, file_name=filename, mime="application/pdf")