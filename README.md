# ♻️ Copenhagen Re-Commerce Matrix

> **B2B Location Intelligence Platform for Circular Fashion, Textile Recycling & Re-Commerce Expansion in Greater Copenhagen.**

[![CI Pipeline](https://github.com/robertomartinengo/copenhagen-recommerce-matrix/actions/workflows/ci.yml/badge.svg)](https://github.com/robertomartinengo/copenhagen-recommerce-matrix/actions)
![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## 📌 Executive Overview

**Copenhagen Re-Commerce Matrix** is an advanced B2B Location Intelligence platform designed to guide circular fashion brands, second-hand boutiques, and textile recycling centers in making data-driven strategic location choices within the Greater Copenhagen area.

Leveraging a multi-criteria mathematical model (**Circular Potential Index - CPI**), the platform analyzes textile waste flows, socio-demographic data (Gen Z density and purchasing power), and market gaps to identify areas with the highest economic and ecological impact potential.

---

## 🧮 Mathematical Model: Circular Potential Index (CPI)

The **CPI** score ($0.0 - 10.0$) is calculated in real-time as a weighted sum of three pillars — Supply, Demographics and Market Gap — with weights that depend on the selected business profile (`cpi_engine.py`, `BUSINESS_PROFILES`):

| Business profile | Supply ($w_1$) | Demographics ($w_2$) | Market Gap ($w_3$) | Sum |
|---|---:|---:|---:|---:|
| Vintage Premium | 0.20 | 0.40 | 0.40 | 1.00 |
| Kilo Sale | 0.50 | 0.30 | 0.20 | 1.00 |
| Upcycling | 0.40 | 0.20 | 0.40 | 1.00 |
| Curated Vintage | 0.33 | 0.33 | 0.34 | 1.00 |

$$\text{CPI} = (w_1 \cdot \text{Supply Score}) + (w_2 \cdot \text{Demographics Score}) + (w_3 \cdot \text{Market Gap Score})$$

* **Supply Score:** textile waste density and recoverable material volume.
* **Demographics Score:** share of the 18-35 target resident base and disposable income (DKK). Derived from `population_gen_z` and `avg_income_dkk` via min-max normalisation (see `D-016` in `DECISIONS.md`).
* **Market Gap Score:** resident population versus existing second-hand stores and collection bins.

---

## 🏛️ System Architecture

The platform is built on a proprietary three-tier architecture consisting of a backend API, a control room dashboard, and a Telegram bot interface. Internal service boundaries, data flows, and infrastructure details are confidential and not disclosed in this document.

---

## 🛠️ Tech Stack & Dependencies

* **Backend & API:** FastAPI, Uvicorn, Pydantic v2
* **Database & Persistence:** Supabase (PostgreSQL)
* **Control Room & Visualization:** Streamlit
* **Reporting & Exports:** fpdf2, Pandas
* **Bot Interface:** python-telegram-bot
* **Code Quality & Testing:** pytest, pytest-cov, mypy, ruff

---

## ✨ Key Features & Deliverables

### 1. 🗺️ Spatial Heatmap (3D Column Map)

3D column map of Greater Copenhagen districts built with PyDeck ColumnLayer on a CARTO basemap, showing CPI score per district. Column height scales with the CPI value; the map follows the browser light/dark theme.

### 2. 📊 District Comparison Table

Side-by-side comparison of districts showing CPI score, Gen Z core population and average income, sorted by CPI for the selected business profile.

### 3. 📄 Automated Executive PDF Generator

Real-time dynamic generation of downloadable B2B summary sheets in PDF format, complete with metropolitan ratings, pillar breakdowns, and strategic retail opening recommendations.

### 4. 🤖 Telegram Bot Assistant

Conversational interface for end-users and retailers:

* **Top zone query:** immediate chat consultation of the top district and key indicators.
* **PDF report:** on-demand generation of the executive PDF report (delivered in chat when the AI service is available, with a deterministic fallback).

---








## 🔒 Lead data and GDPR

The Telegram lead funnel shows the privacy notice and requires explicit consent before collecting or storing personal data. The bot stores the name, professional email, Telegram ID/username, selected business profile and district together with the accepted notice version and timestamp. Personal data is never included in AI prompts.

Users can delete their data with the Telegram command `/delete_my_data`. The API also exposes `DELETE /leads/{telegram_user_id}`, protected by the `X-Lead-Delete-Token` header. Identifying fields are anonymised after 12 months. See [PRIVACY.md](PRIVACY.md) for the complete notice.

## 🧪 Testing & Quality Assurance

*The project uses pytest for unit tests, ruff for linting and mypy for static type checking:*

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
