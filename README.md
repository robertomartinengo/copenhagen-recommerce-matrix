# ♻️ Copenhagen Re-Commerce Matrix

> **B2B Location Intelligence Platform for Circular Fashion, Textile Recycling & Re-Commerce Expansion in Greater Copenhagen.**

[![CI Pipeline](https://github.com/robertomartinengo/copenhagen-recommerce-matrix/actions/workflows/ci.yml/badge.svg)](https://github.com/robertomartinengo/copenhagen-recommerce-matrix/actions)
![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)
![Code Style](https://img.shields.io/badge/type--check-mypy%20100%25-blue)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## 📌 Executive Overview

**Copenhagen Re-Commerce Matrix** is an advanced B2B Location Intelligence platform designed to guide circular fashion brands, second-hand boutiques, and textile recycling centers in making data-driven strategic location choices within the Greater Copenhagen area.

Leveraging a multi-criteria mathematical model (**Circular Potential Index - CPI**), the platform analyzes textile waste flows, socio-demographic data (Gen Z density and purchasing power), and market gaps to identify areas with the highest economic and ecological impact potential.

---

## 🧮 Mathematical Model: Circular Potential Index (CPI)

The **CPI** score ($0.0 - 10.0$) is calculated in real-time using a weighted combination of three core pillars:

$$\text{CPI} = (w_1 \cdot \text{Supply Score}) + (w_2 \cdot \text{Demographics Score}) + (w_3 \cdot \text{Market Gap Score})$$

* **Supply Score ($w_1 = 0.40$):** Textile waste density and annual recoverable material volume (t/year).
* **Demographics Score ($w_2 = 0.35$):** Concentration of the Gen Z/Millennial target demographic and average disposable income (DKK).
* **Market Gap Score ($w_3 = 0.25$):** Market opportunity measured by the ratio of the resident population to existing second-hand stores or collection bins.

---

## 🏛️ System Architecture

*The system is built on a modern, modular three-tier architecture:*

```text
[ Supabase PostgreSQL ]
         │
         ▼
[ FastAPI Backend Engine ] ──(REST API)──► [ Pytest & Mypy CI/CD Pipeline ]
         │
         ├──► [ Streamlit Technical Control Room ] (Spatial GeoJSON Heatmap & B2B Radar)
         ├──► [ Executive PDF Engine ] (FPDF2 Automated Report Generation)
         └──► [ Freemium Telegram Bot ] (Interactive Retail Decision Assistant)
```

---

## 🛠️ Tech Stack & Dependencies

* **Backend & API:** FastAPI, Uvicorn, Pydantic v2
* **Database & Persistence:** Supabase (PostgreSQL)
* **Control Room & Visualization:** Streamlit, Plotly Express, Plotly Graph Objects, GeoJSON
* **Reporting & Exports:** fpdf2, Pandas
* **Bot Interface:** python-telegram-bot
* **Code Quality & Testing:** pytest, pytest-cov, mypy
* **Containerization:** Docker, Docker Compose

---

## ✨ Key Features & Deliverables

### 1. 🗺️ Spatial Heatmap (GeoJSON Polygonal Choropleth)

High-precision geographical visualization of the 11 districts of Greater Copenhagen and Frederiksberg, featuring adaptive color gradients based on the CPI score.

### 2. ⚔️ Side-by-Side B2B Benchmark & Radar Chart

Direct analytical comparison between two selected districts (Textile Raw Material, Gen Z Target, Market Opportunity) using side-by-side bar charts and a two-dimensional radar profile.

### 3. 📄 Automated Executive PDF Generator

Real-time dynamic generation of downloadable B2B summary sheets in PDF format, complete with metropolitan ratings, pillar breakdowns, and strategic retail opening recommendations.

### 4. 🤖 Freemium Telegram Bot Assistant

Direct conversational interface designed for the end-user/retailer:

* **Free Tier:** Immediate chat consultation of the top zone and key indicators.
* **Premium Tier:** Automatic generation and delivery of the full Executive PDF Report directly in the chat.

---

## 🚀 Getting Started

### 📋 Prerequisites

* Python `3.11+`
* Docker & Docker Compose *(optional for containerization)*

### ⚙️ Local Setup

1. **Clone the repository and set up the virtual environment:**

   ```bash
   git clone https://github.com/robertomartinengo/copenhagen-recommerce-matrix.git
   cd copenhagen-recommerce-matrix
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**

   ```bash
   cp .env.example .env
   ```

   *Insert your real parameters in* `.env` *(*`SUPABASE_URL`*,* `SUPABASE_KEY`*,* `TELEGRAM_BOT_TOKEN`*).*

4. **Run the Control Room and API:**

   ```bash
   # Terminal 1 (Backend API)
   uvicorn main:app --reload --port 8000

   # Terminal 2 (Dashboard Streamlit)
   streamlit run dashboard.py
   ```

---

## 🐳 Docker Deployment

*Run the entire isolated stack (Backend + Dashboard + Telegram Bot) with a single command:*

```bash
docker-compose up --build
```

---

## 🧪 Testing & Quality Assurance

*The project guarantees a high standard of code quality with 100% test coverage:*

```bash
# Run the test suite with coverage report
pytest --cov=. --cov-report=term-missing

# Run static type checking
mypy cpi_engine.py schemas.py --ignore-missing-imports
```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
