import inspect
import os

import pandas as pd
import pydeck as pdk
import requests
import streamlit as st
from dotenv import load_dotenv
from streamlit_theme import st_theme

from cpi_engine import calculate_dynamic_cpi

load_dotenv()

API_URL = os.getenv("API_URL", "https://copenhagen-recommerce-matrix.onrender.com")

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Copenhagen Re-Commerce Matrix | B2B Dashboard",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --- COMPATIBILITA' VERSIONI STREAMLIT ---
# use_container_width e' stato sostituito da width="stretch" nelle versioni recenti.
def stretch_kwargs(fn) -> dict:
    if "width" in inspect.signature(fn).parameters:
        return {"width": "stretch"}
    return {"use_container_width": True}


# --- TEMA BROWSER (chiaro / scuro) ---
MAP_STYLES = {
    "light": "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    "dark": "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
}


def _is_dark_hex(color: str):
    """True/False in base alla luminosita' di un colore #rrggbb, None se non leggibile."""
    try:
        h = color.lstrip("#")
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        return (0.299 * r + 0.587 * g + 0.114 * b) < 128
    except Exception:
        return None


def get_browser_theme() -> str:
    """Tema attivo nel browser: 'light' o 'dark'.

    st_theme() e' un componente che si aggiorna anche quando l'utente cambia
    tema dal menu Settings (st.context.theme.type no: la documentazione di
    Streamlit avverte che puo' essere sbagliato durante il cambio di tema).
    Al primo caricamento il componente puo' restituire None: in quel caso si
    usa st.context.theme.type e poi theme.base di config.toml.
    """
    theme = st_theme()
    if theme:
        base = theme.get("base")
        if base in MAP_STYLES:
            return base
        dark = _is_dark_hex(str(theme.get("backgroundColor", "")))
        if dark is not None:
            return "dark" if dark else "light"
    try:
        fallback = st.context.theme.type
    except Exception:
        fallback = st.get_option("theme.base")
    return fallback if fallback in MAP_STYLES else "light"


THEME = get_browser_theme()

# --- CSS EXECUTIVE (Stondatura Universale) ---
st.markdown(
    """
    <style>
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
        border-bottom: 1px solid rgba(128, 128, 128, 0.25);
        border-left: 1px solid rgba(128, 128, 128, 0.25);
        border-right: 1px solid rgba(128, 128, 128, 0.25);
    }
    hr { border-color: #6E8E80; opacity: 0.2; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- COORDINATE DI BACKUP (Tutti i distretti di Copenaghen) ---
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
    "brønshøj-husum": (55.7100, 12.4800),
}


# --- RECUPERO DATI API ---
# Le eccezioni non vengono messe in cache: un errore temporaneo (es. cold start
# di Render) non resta "bloccato" per 60 secondi.
@st.cache_data(ttl=60, show_spinner="Caricamento dati dall'API…")
def fetch_raw_zones():
    response = requests.get(f"{API_URL}/zones", timeout=40)
    response.raise_for_status()
    return response.json()


# --- GRADIENTE SALVIA, DIVERSO PER TEMA ---
# Tema chiaro: punteggio alto = verde scuro (contrasta con la mappa chiara).
# Tema scuro: punteggio alto = verde luminoso (contrasta con la mappa scura).
SAGE_PALETTES = {
    "light": [
        (8.2, [47, 79, 79, 255]),
        (7.4, [90, 125, 110, 255]),
        (6.6, [140, 172, 156, 255]),
        (6.0, [185, 208, 196, 255]),
        (-float("inf"), [214, 228, 220, 255]),
    ],
    "dark": [
        (8.2, [170, 225, 200, 255]),
        (7.4, [120, 175, 150, 255]),
        (6.6, [85, 130, 112, 255]),
        (6.0, [62, 95, 82, 255]),
        (-float("inf"), [48, 70, 62, 255]),
    ],
}

LINE_COLORS = {
    "light": [47, 79, 79, 120],
    "dark": [255, 255, 255, 90],
}


def get_sage_gradient(score: float, theme: str = "light"):
    for threshold, color in SAGE_PALETTES[theme]:
        if score >= threshold:
            return color
    return SAGE_PALETTES[theme][-1][1]


# --- SIDEBAR: FILTRI DINAMICI ---
st.sidebar.title("♻️ Re-Commerce Matrix")
st.sidebar.markdown("Seleziona il profilo per ricalcolare il potenziale:")

profile_options = {
    "💼 Boutique / Lusso (Vintage Premium)": "vintage_premium",
    "⚖️ Mercatino a Peso (Kilo Sale)": "kilo_sale",
    "✂️ Laboratorio Sartoriale (Upcycling)": "upcycling",
    "🛍️ Pop-Up di Quartiere (Curated Vintage)": "curated_vintage",
}

selected_label = st.sidebar.selectbox("Modello di Business:", list(profile_options.keys()))
active_profile_key = profile_options[selected_label]

api_error = None
try:
    raw_zones = fetch_raw_zones()
except Exception as e:
    raw_zones = []
    api_error = str(e)

# --- ELABORAZIONE DATI ---
processed_zones = []
for zone in raw_zones:
    cpi_res = calculate_dynamic_cpi(zone, business_type=active_profile_key)
    z_data = zone.copy()
    score = cpi_res["cpi_score"]
    z_data["cpi_score"] = score

    name_lower = z_data["name"].lower().strip()
    if name_lower in COPENHAGEN_COORDS:
        z_data["lat"], z_data["lon"] = COPENHAGEN_COORDS[name_lower]

    # Scarta zone senza coordinate valide (None, 0 o assenti)
    if not z_data.get("lat") or not z_data.get("lon"):
        continue

    z_data["elevation"] = max((score - 4.5), 0.5) * 800
    z_data["fill_color"] = get_sage_gradient(score, THEME)
    # Valori gia' formattati per il tooltip (altrimenti mostra float lunghi)
    z_data["cpi_label"] = f"{score:.2f} / 10"
    z_data["gen_z_label"] = f"{z_data['population_gen_z']:,.0f}"
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
            delta=f"{top_zone['cpi_score']:.2f} / 10",
            delta_color="off",
        )
    with col2:
        st.metric(
            label="👥 Target Gen Z Core",
            value=f"{top_zone['population_gen_z']:,.0f}",
            delta=f"Residenti a {top_zone['name']}",
            delta_color="off",
        )
    with col3:
        st.metric(
            label="💰 Reddito Medio Pro-Capite",
            value=f"{top_zone['avg_income_dkk']:,.0f} DKK",
            delta="Annuo",
            delta_color="off",
        )

    st.write("")

    # --- MAPPA 3D E TABELLA ---
    PANEL_HEIGHT = 460

    col_map, col_table = st.columns([1.5, 1])

    with col_map:
        st.subheader("📍 Topografia del Valore B2B")

        layer = pdk.Layer(
            "ColumnLayer",
            data=df,
            get_position=["lon", "lat"],
            get_elevation="elevation",
            elevation_scale=1,
            radius=400,
            disk_resolution=40,
            extruded=True,
            get_fill_color="fill_color",
            stroked=True,
            get_line_color=LINE_COLORS[THEME],
            line_width_min_pixels=1,
            pickable=True,
            auto_highlight=True,
        )

        view_state = pdk.ViewState(
            latitude=55.675,
            longitude=12.56,
            zoom=10.5,
            pitch=50,
            bearing=-15,
        )

        r = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={
                "html": "<b>{name}</b><br/>CPI Score: {cpi_label}<br/>Gen Z: {gen_z_label}",
                "style": {
                    "backgroundColor": "#6E8E80",
                    "color": "white",
                    "borderRadius": "8px",
                },
            },
            map_style=MAP_STYLES[THEME],
        )

        # key legata al tema: forza il ricaricamento della mappa al cambio tema
        st.pydeck_chart(r, height=PANEL_HEIGHT, key=f"map_{THEME}", **stretch_kwargs(st.pydeck_chart))

    with col_table:
        st.subheader("📊 Classifica Distretti")

        display_df = df[["name", "cpi_score", "population_gen_z", "avg_income_dkk"]].copy()
        display_df.columns = ["Distretto", "Indice CPI", "Gen Z Core", "Reddito (DKK)"]
        display_df["Indice CPI"] = display_df["Indice CPI"].round(2)
        display_df["Gen Z Core"] = display_df["Gen Z Core"].map("{:,.0f}".format)
        display_df["Reddito (DKK)"] = display_df["Reddito (DKK)"].map("{:,.0f}".format)

        st.dataframe(
            display_df,
            height=PANEL_HEIGHT - 40,
            hide_index=True,
            **stretch_kwargs(st.dataframe),
        )

else:
    if api_error:
        st.error(
            "⚠️ Impossibile contattare l'API (il servizio su Render potrebbe essere in "
            f"avvio, riprova tra qualche secondo).\n\nDettaglio: {api_error}"
        )
    else:
        st.error("⚠️ Nessun distretto elaborato. Verifica i dati restituiti dall'API.")

st.divider()
st.caption("Copenhagen Re-Commerce Matrix B2B Platform — Streamlit Dashboard")