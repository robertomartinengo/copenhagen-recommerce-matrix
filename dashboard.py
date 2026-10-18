import json
import os
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# Configurazione Pagina
st.set_page_config(
    page_title="Copenhagen Re-Commerce Matrix",
    page_icon="♻️",
    layout="wide"
)

API_URL = os.getenv("API_URL", "http://localhost:8000")

# Caricamento GeoJSON
@st.cache_data
def load_geojson():
    geojson_path = "copenhagen_districts.geojson"
    if os.path.exists(geojson_path):
        with open(geojson_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

geojson_data = load_geojson()

st.title("♻️ Copenhagen Re-Commerce Matrix")
st.caption("B2B Location Intelligence Platform for Circular Fashion & Textile Recycling")

# Sidebar - What-If Engine
st.sidebar.header("🎛️ What-If Simulation Engine")
st.sidebar.markdown("Regola i pesi per ricalcolare il **Circular Potential Index (CPI)** in tempo reale:")

w_supply = st.sidebar.slider("Peso Supply Rifiuti Tessili (w1)", 0.0, 1.0, 0.40, 0.05)
w_demo = st.sidebar.slider("Peso Demografia Gen Z / Reddito (w2)", 0.0, 1.0, 0.35, 0.05)
w_gap = st.sidebar.slider("Peso Vuoto di Mercato (w3)", 0.0, 1.0, 0.25, 0.05)

total_weight = w_supply + w_demo + w_gap
if abs(total_weight - 1.0) > 0.01:
    st.sidebar.warning(f"⚠️ La somma dei pesi è {total_weight:.2f}. Per la massima accuratezza, la somma dovrebbe essere 1.00.")

# Fetch Dati da API Backend
@st.cache_data(ttl=60)
def fetch_zones(w1: float, w2: float, w3: float):
    try:
        response = requests.get(
            f"{API_URL}/zones",
            params={"w_supply": w1, "w_demo": w2, "w_gap": w3},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Errore di connessione al Backend API ({API_URL}): {e}")
        return []

data = fetch_zones(w_supply, w_demo, w_gap)

if not data:
    st.warning("Nessun dato disponibile. Assicurati che il backend FastAPI sia avviato.")
    st.stop()

df = pd.DataFrame(data)

# Mappatura sicura delle colonne
def get_col(df_obj, candidates):
    for c in candidates:
        if c in df_obj.columns:
            return c
    return None

col_supply_score = get_col(df, ["waste_supply_score", "supply_score"])
col_demo_score = get_col(df, ["demographics_score", "demo_score"])
col_gap_score = get_col(df, ["market_gap_score", "gap_score"])
col_gen_z = get_col(df, ["population_gen_z", "gen_z_percentage", "gen_z_share"])
col_income = get_col(df, ["avg_income_dkk", "avg_annual_income_eur"])

# Normalizzazione visualizzazione Gen Z
def format_gen_z(val):
    if val is None or pd.isna(val):
        return "N/A"
    if val > 100:
        return f"{val:,.0f} ab."  # Se rappresenta la popolazione assoluta
    return f"{val:.1f}%"

# Calcolo Rank se non presente
if "rank" not in df.columns:
    df["rank"] = df["cpi_score"].rank(ascending=False, method="min").astype(int)
    df = df.sort_values("rank")

# KPI Summary Cards
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
top_zone = df.iloc[0]
kpi1.metric("Top Strategic District", top_zone["name"], f"CPI: {top_zone['cpi_score']:.1f}")
kpi2.metric("Media CPI Metropolitano", f"{df['cpi_score'].mean():.1f}")

gen_z_avg = df[col_gen_z].mean() if col_gen_z else None
income_avg = df[col_income].mean() if col_income else None

kpi3.metric("Media Gen Z Area", format_gen_z(gen_z_avg))
kpi4.metric("Reddito Medio Area", f"{income_avg:,.0f} DKK" if income_avg else "N/A")

st.divider()

# Layout Mappa Poligonale Heatmap & Classifica Side-by-Side
col_map, col_rank = st.columns([3, 2])

with col_map:
    st.subheader("🗺️ Spatial Heatmap (CPI Score per Distretto)")
    if geojson_data:
        has_choropleth_map = hasattr(px, "choropleth_map")
        
        hover_dict = {"cpi_score": ":.1f"}
        if col_supply_score and col_supply_score in df.columns:
            hover_dict[col_supply_score] = ":.1f"
        if col_gap_score and col_gap_score in df.columns:
            hover_dict[col_gap_score] = ":.1f"

        map_kwargs = {
            "data_frame": df,
            "geojson": geojson_data,
            "locations": "name",
            "featureidkey": "properties.name",
            "color": "cpi_score",
            "color_continuous_scale": "Viridis",
            "range_color": (df["cpi_score"].min(), df["cpi_score"].max()),
            "zoom": 10.5,
            "center": {"lat": 55.6761, "lon": 12.5683},
            "opacity": 0.65,
            "hover_name": "name",
            "hover_data": hover_dict,
            "labels": {"cpi_score": "Punteggio CPI"}
        }

        if has_choropleth_map:
            map_kwargs["map_style"] = "carto-positron"
            fig_map = px.choropleth_map(**map_kwargs)
        else:
            map_kwargs["mapbox_style"] = "carto-positron"
            fig_map = px.choropleth_mapbox(**map_kwargs)

        fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=450)
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("Mappa poligonale non disponibile (GeoJSON mancante).")

with col_rank:
    st.subheader("🏆 Leaderboard Distretti")
    rank_cols = ["rank", "name", "cpi_score"]
    for c in [col_supply_score, col_gap_score]:
        if c and c in df.columns and c not in rank_cols:
            rank_cols.append(c)
            
    st.dataframe(
        df[rank_cols],
        column_config={
            "rank": st.column_config.NumberColumn("Rank", format="#%d"),
            "name": "Distretto",
            "cpi_score": st.column_config.NumberColumn("CPI", format="%.1f"),
            col_supply_score: st.column_config.NumberColumn("Supply Score", format="%.1f"),
            col_gap_score: st.column_config.NumberColumn("Market Gap Score", format="%.1f"),
        },
        hide_index=True,
        use_container_width=True,
        height=420
    )

st.divider()

# Grafico a barre componenti CPI (Escludendo cpi_score)
st.subheader("📊 Decomposizione del Punteggio CPI per Distretto")
bar_y_cols = [c for c in [col_supply_score, col_demo_score, col_gap_score] if c and c in df.columns and c != "cpi_score"]

fig_bar = px.bar(
    df,
    x="name",
    y=bar_y_cols,
    title="Contributo delle Componenti al CPI Totale",
    labels={"value": "Punteggio Componente", "variable": "Componente", "name": "Distretto"},
    barmode="stack",
    height=400
)
st.plotly_chart(fig_bar, use_container_width=True)

# Deep-Dive Ispettore per Singolo Distretto
st.divider()
st.subheader("🔍 Ispettore Dettagliato Distretto")
selected_district = st.selectbox("Seleziona un distretto da analizzare:", df["name"].tolist())
district_data = df[df["name"] == selected_district].iloc[0]

d_col1, d_col2, d_col3, d_col4 = st.columns(4)
d_col1.metric("CPI Score", f"{district_data['cpi_score']:.1f}")
d_col2.metric("Gen Z Share / Popolazione", format_gen_z(district_data[col_gen_z]) if col_gen_z else "N/A")
d_col3.metric("Reddito Medio", f"{district_data[col_income]:,.0f} DKK" if col_income else "N/A")
d_col4.metric("Market Gap Score", f"{district_data[col_gap_score]:.1f}" if col_gap_score and col_gap_score in district_data else "N/A")

# Export CSV Button
st.divider()
csv_data = df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Scarica Report Matrice in CSV",
    data=csv_data,
    file_name="copenhagen_recommerce_matrix.csv",
    mime="text/csv"
)