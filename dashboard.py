import json
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from pdf_generator import generate_district_pdf

# Configurazione Pagina
st.set_page_config(
    page_title="Copenhagen Re-Commerce Matrix",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = os.getenv("API_URL", "http://localhost:8000")

# Funzione di utilità per la mappatura sicura delle colonne
def get_col(df_obj, candidates):
    for c in candidates:
        if c in df_obj.columns:
            return c
    return None

# Caricamento GeoJSON
@st.cache_data
def load_geojson():
    geojson_path = "copenhagen_districts.geojson"
    if os.path.exists(geojson_path):
        with open(geojson_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

geojson_data = load_geojson()

# Intestazione Dashboard
st.title("♻️ Copenhagen Re-Commerce Matrix")
st.caption("B2B Location Intelligence & Circular Economy Decision Support Platform")

# ---------------------------------------------------------
# SIDEBAR: What-If Engine & Filtri
# ---------------------------------------------------------
st.sidebar.header("⚙️ What-If Simulation Engine")
st.sidebar.markdown("Regola i pesi per ricalcolare il **CPI** in tempo reale:")

w_supply = st.sidebar.slider("Peso Supply Rifiuti Tessili (w1)", 0.0, 1.0, 0.40, 0.05)
w_demo = st.sidebar.slider("Peso Demografia Gen Z / Reddito (w2)", 0.0, 1.0, 0.35, 0.05)
w_gap = st.sidebar.slider("Peso Vuoto di Mercato (w3)", 0.0, 1.0, 0.25, 0.05)

total_weight = w_supply + w_demo + w_gap
if abs(total_weight - 1.0) > 0.01:
    st.sidebar.warning(f"⚠️ Somma pesi: {total_weight:.2f}. Consigliato 1.00.")

st.sidebar.divider()
st.sidebar.header("🔍 Filtri Analitici")
min_cpi = st.sidebar.slider("Soglia Minima CPI Score", 0.0, 10.0, 0.0, 0.5)

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

raw_data = fetch_zones(w_supply, w_demo, w_gap)
if not raw_data:
    st.warning("Nessun dato disponibile. Verificare che il backend FastAPI sia attivo.")
    st.stop()

df = pd.DataFrame(raw_data)

# Mappatura Colonne
col_supply_score = get_col(df, ["waste_supply_score", "supply_score"]) or "supply_score"
col_demo_score = get_col(df, ["demographics_score", "demo_score"]) or "demographics_score"
col_gap_score = get_col(df, ["market_gap_score", "gap_score"]) or "market_gap_score"
col_gen_z = get_col(df, ["population_gen_z", "gen_z_percentage"])
col_income = get_col(df, ["avg_income_dkk", "avg_annual_income_eur"])

# Gestione Ranks e Filtro Minimo
df["rank"] = df["cpi_score"].rank(ascending=False, method="min").astype(int)
df_filtered = df[df["cpi_score"] >= min_cpi].sort_values("rank")

if df_filtered.empty:
    st.warning("Nessun distretto soddisfa i criteri del filtro impostato.")
    st.stop()

def format_gen_z(val):
    if val is None or pd.isna(val):
        return "N/A"
    return f"{val:,.0f} ab." if val > 100 else f"{val:.1f}%"

# ---------------------------------------------------------
# 1. EXECUTIVE KPI SUMMARY
# ---------------------------------------------------------
top_zone = df_filtered.iloc[0]
avg_cpi = df["cpi_score"].mean()

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    with st.container(border=True):
        st.metric("Top Strategic Zone", top_zone["name"], f"CPI: {top_zone['cpi_score']:.1f}")
with kpi2:
    with st.container(border=True):
        st.metric("Media CPI Area", f"{avg_cpi:.1f}", f"Δ Top: +{(top_zone['cpi_score'] - avg_cpi):.1f}")
with kpi3:
    with st.container(border=True):
        gen_z_tot = df[col_gen_z].sum() if col_gen_z else 0
        st.metric("Bacino Gen Z Totale", f"{gen_z_tot:,.0f}" if gen_z_tot > 0 else "N/A")
with kpi4:
    with st.container(border=True):
        inc_avg = df[col_income].mean() if col_income else 0
        st.metric("Reddito Medio Area", f"{inc_avg:,.0f} DKK" if inc_avg else "N/A")

st.divider()

# ---------------------------------------------------------
# 2. SPATIAL HEATMAP & LEADERBOARD
# ---------------------------------------------------------
col_map, col_rank = st.columns([3, 2])

with col_map:
    st.subheader("🗺️ Spatial Heatmap (CPI per Distretto)")
    if geojson_data:
        has_choropleth = hasattr(px, "choropleth_map")
        map_kwargs = {
            "data_frame": df_filtered,
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
            "hover_data": {"cpi_score": ":.1f", col_supply_score: ":.1f", col_gap_score: ":.1f"},
            "labels": {"cpi_score": "CPI Score"}
        }
        if has_choropleth:
            map_kwargs["map_style"] = "carto-positron"
            fig_map = px.choropleth_map(**map_kwargs)
        else:
            map_kwargs["mapbox_style"] = "carto-positron"
            fig_map = px.choropleth_mapbox(**map_kwargs)
        fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=420)
        st.plotly_chart(fig_map, width="stretch")
    else:
        st.warning("GeoJSON non disponibile.")

with col_rank:
    st.subheader("🏆 Leaderboard Distrettuale")
    rank_cols = ["rank", "name", "cpi_score", col_supply_score, col_gap_score]
    st.dataframe(
        df_filtered[rank_cols],
        column_config={
            "rank": st.column_config.NumberColumn("Rank", format="#%d"),
            "name": "Distretto",
            "cpi_score": st.column_config.NumberColumn("CPI", format="%.1f"),
            col_supply_score: st.column_config.NumberColumn("Supply", format="%.1f"),
            col_gap_score: st.column_config.NumberColumn("Market Gap", format="%.1f"),
        },
        hide_index=True,
        width="stretch",
        height=400
    )

st.divider()

# ---------------------------------------------------------
# 3. NUOVO GRAFICO: QUADRANT MATRIX (Oceano Blu)
# ---------------------------------------------------------
st.subheader("🎯 Matrice di Opportunità: Supply vs Market Gap")
st.caption("I distretti nel **quadrante in alto a destra** rappresentano le opportunita 'Oceano Blu' (alto volume tessile + scarso presidio della concorrenza).")

avg_supply = df[col_supply_score].mean()
avg_gap = df[col_gap_score].mean()

fig_scatter = px.scatter(
    df_filtered,
    x=col_gap_score,
    y=col_supply_score,
    size=col_gen_z if col_gen_z else None,
    color="cpi_score",
    text="name",
    color_continuous_scale="Viridis",
    labels={
        col_gap_score: "Opportunità di Mercato (Market Gap)",
        col_supply_score: "Disponibilità Materia Prima (Supply)",
        "cpi_score": "CPI Score"
    },
    size_max=35,
    height=450
)

# Linee di quadrante per evidenziare le zone target
fig_scatter.add_vline(x=avg_gap, line_dash="dash", line_color="gray", annotation_text="Media Gap")
fig_scatter.add_hline(y=avg_supply, line_dash="dash", line_color="gray", annotation_text="Media Supply")
fig_scatter.update_traces(textposition="top center")
fig_scatter.update_layout(margin=dict(t=30, b=30, l=30, r=30))

st.plotly_chart(fig_scatter, width="stretch")

st.divider()

# ---------------------------------------------------------
# 4. BENCHMARK SIDE-BY-SIDE
# ---------------------------------------------------------
st.subheader("⚔️ Benchmark Distrettuale Side-by-Side")
b_col1, b_col2 = st.columns(2)
district_list = df["name"].tolist()

with b_col1:
    dist1_name = st.selectbox("Seleziona Distretto A:", district_list, index=0)
with b_col2:
    dist2_name = st.selectbox("Seleziona Distretto B:", district_list, index=min(1, len(district_list)-1))

d1_data = df[df["name"] == dist1_name].iloc[0]
d2_data = df[df["name"] == dist2_name].iloc[0]

categories = ["Materia Prima Tessile", "Target Gen Z", "Opportunità di Mercato"]
val1 = [float(d1_data[col_supply_score]), float(d1_data[col_demo_score]), float(d1_data[col_gap_score])]
val2 = [float(d2_data[col_supply_score]), float(d2_data[col_demo_score]), float(d2_data[col_gap_score])]

tab_bars, tab_radar = st.tabs(["📊 Confronto a Barre", "🕸️ Profilo Radar"])

with tab_bars:
    bench_df = pd.DataFrame({
        "Indicatore": categories * 2,
        "Punteggio (0-10)": val1 + val2,
        "Distretto": [dist1_name] * 3 + [dist2_name] * 3
    })
    fig_grouped = px.bar(
        bench_df,
        x="Indicatore",
        y="Punteggio (0-10)",
        color="Distretto",
        barmode="group",
        text_auto=".1f",
        color_discrete_sequence=["#1f77b4", "#ff7f0e"],
        height=360
    )
    fig_grouped.update_layout(yaxis_range=[0, 10], margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig_grouped, width="stretch")

with tab_radar:
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=val1 + [val1[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(31, 119, 180, 0.2)',
        name=dist1_name,
        line=dict(color='#1f77b4', width=3)
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=val2 + [val2[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(255, 127, 14, 0.2)',
        name=dist2_name,
        line=dict(color='#ff7f0e', width=3)
    ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
        showlegend=True,
        height=360,
        margin=dict(t=20, b=20, l=40, r=40)
    )
    st.plotly_chart(fig_radar, width="stretch")

# Differenziali
st.markdown(f"#### 📊 Differenziale: **{dist1_name}** vs **{dist2_name}**")
d_col1, d_col2, d_col3 = st.columns(3)
cpi_diff = d1_data["cpi_score"] - d2_data["cpi_score"]
d_col1.metric("Delta CPI Score", f"{d1_data['cpi_score']:.1f}", f"{cpi_diff:+.1f} vs {dist2_name}")

if col_gen_z and col_gen_z in d1_data:
    gz_diff = d1_data[col_gen_z] - d2_data[col_gen_z]
    d_col2.metric("Delta Gen Z", format_gen_z(d1_data[col_gen_z]), f"{gz_diff:+,.0f} ab. vs {dist2_name}")

if col_income and col_income in d1_data:
    inc_diff = d1_data[col_income] - d2_data[col_income]
    d_col3.metric("Delta Reddito Medio", f"{d1_data[col_income]:,.0f} DKK", f"{inc_diff:+,.0f} DKK vs {dist2_name}")

# ---------------------------------------------------------
# 5. ISPETTORE E DOWNLOAD REPORT
# ---------------------------------------------------------
st.divider()
st.subheader("🔍 Ispettore Dettagliato & Export Report")

insp_col, dl_col1, dl_col2 = st.columns([2, 1, 1])

with insp_col:
    selected_district = st.selectbox("Seleziona distretto per il Report PDF:", df["name"].tolist())
    district_data = df[df["name"] == selected_district].iloc[0]

with dl_col1:
    st.write("")
    st.write("")
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Scarica Matrice CSV",
        data=csv_data,
        file_name="copenhagen_recommerce_matrix.csv",
        mime="text/csv",
        width="stretch"
    )

with dl_col2:
    st.write("")
    st.write("")
    pdf_filename = f"Executive_Report_{selected_district.replace(' ', '_')}.pdf"
    generate_district_pdf(district_data.to_dict(), filename=pdf_filename)
    if os.path.exists(pdf_filename):
        with open(pdf_filename, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()
        st.download_button(
            label=f"📄 Scarica PDF ({selected_district})",
            data=pdf_bytes,
            file_name=pdf_filename,
            mime="application/pdf",
            width="stretch"
        )