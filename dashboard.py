import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Copenhagen Re-Commerce Matrix",
    page_icon="♻️",
    layout="wide"
)

API_URL = "http://127.0.0.1:8000"

st.title("♻️ Copenhagen Re-Commerce Matrix")
st.markdown("### Location Intelligence & Circular Fashion Analytics (Greater Copenhagen & Frederiksberg)")

# Sidebar per la simulazione What-If
st.sidebar.header("🎛️ Parametri Simulazione CPI")
w_supply = st.sidebar.slider("Peso Supply (Rifiuti/Tessile)", 0.0, 1.0, 0.40, 0.05)
w_demo = st.sidebar.slider("Peso Demografia (Gen Z / Income)", 0.0, 1.0, 0.35, 0.05)
w_gap = st.sidebar.slider("Peso Vuoto di Mercato", 0.0, 1.0, 0.25, 0.05)

total_w = round(w_supply + w_demo + w_gap, 2)

if total_w != 1.0:
    st.sidebar.error(f"⚠️ La somma dei pesi deve essere pari a 1.0 (Attuale: {total_w})")
else:
    st.sidebar.success("✅ Pesi bilanciati correttamente")

# Fetch dati dal backend FastAPI
try:
    if total_w == 1.0 and (w_supply != 0.40 or w_demo != 0.35 or w_gap != 0.25):
        # Chiamata all'endpoint di simulazione
        res = requests.post(
            f"{API_URL}/simulate-cpi",
            json={
                "weight_supply": w_supply,
                "weight_demographics": w_demo,
                "weight_market_gap": w_gap
            }
        )
        data = res.json()["results"]
        df = pd.DataFrame(data)
        score_col = "simulated_cpi_score"
    else:
        # Fetch dati baseline dal database
        res = requests.get(f"{API_URL}/zones")
        data = res.json()
        df = pd.DataFrame(data)
        score_col = "cpi_score"

    # KPI Top Metrics
    top_zone = df.iloc[0]
    col1, col2, col3 = st.columns(3)
    col1.metric("Top Zone", top_zone["name"])
    col2.metric("Punteggio CPI", f"{top_zone[score_col]:.2f}")
    col3.metric("Zone Monitorate", len(df))

    st.markdown("---")

    # Grafico a barre interattivo
    fig = px.bar(
        df,
        x="name",
        y=score_col,
        color=score_col,
        title="Classifica Circular Potential Index (CPI) per Quartiere",
        labels={"name": "Quartiere", score_col: "CPI Score"},
        color_continuous_scale="Viridis",
        text_auto=".2f"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Tabella Dati
    st.subheader("📊 Matrice Dati Operativa")
    st.dataframe(df, use_container_width=True)

    # Download CSV Report
    st.markdown("---")
    csv_res = requests.get(f"{API_URL}/export/csv")
    if csv_res.status_code == 200:
        st.download_button(
            label="📥 Scarica Report Matrice CSV",
            data=csv_res.content,
            file_name="copenhagen_recommerce_matrix.csv",
            mime="text/csv"
        )

except Exception as e:
    st.error(f"Impossibile collegarsi al backend API su {API_URL}. Verifica che Uvicorn sia attivo!")