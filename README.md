# ♻️ Copenhagen Re-Commerce Matrix

> **B2B Location Intelligence Platform for Circular Fashion, Textile Recycling & Re-Commerce Expansion in Greater Copenhagen.**

[![CI Pipeline](https://github.com/robertomartinengo/copenhagen-recommerce-matrix/actions/workflows/ci.yml/badge.svg)](https://github.com/robertomartinengo/copenhagen-recommerce-matrix/actions)
![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)
![Code Style](https://img.shields.io/badge/type--check-mypy%20100%25-blue)
![License](https://img.shields.io/badge/license-Proprietary-red.svg)

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

The platform is built on a proprietary three-tier architecture consisting of a backend API, a control room dashboard, and a Telegram bot interface. Internal service boundaries, data flows, and infrastructure details are confidential and not disclosed in this document.

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

This software is proprietary and confidential. All rights reserved.
See `LICENSE` for full terms. No part of this software may be copied,
modified, or distributed without written permission from the copyright holder.
