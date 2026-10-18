# ♻️ Copenhagen Re-Commerce Matrix

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.103.1-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28.0-FF4B4B.svg?logo=streamlit)](https://streamlit.io/)
[![Supabase](https://img.shields.io/badge/Supabase-Database-3ECF8E.svg?logo=supabase)](https://supabase.com/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Location Intelligence & Circular Fashion Analytics Platform for Greater Copenhagen & Frederiksberg.

> Developed as a strategic business analytics tool for the **International AI Startup Challenge (IASC)** and the **Blue Ocean Entrepreneurship Competition**.

---

## 🤖 AI-Assisted Learning & Development
This full-stack project was developed with the active support of AI (Large Language Models) as an advanced pair-programming assistant. Integrating AI into the workflow allowed me to accelerate architectural design, explore enterprise-grade engineering practices (like Docker containerization, CI/CD automated testing pipelines, and RESTful API structures), and focus deeply on the mathematical modeling and location intelligence logic required for circular economy decision-making.

---

## 📌 Features
* **Circular Potential Index (CPI) Engine:** Multi-criteria scoring algorithm across 11 metropolitan districts (10 Copenhagen Bydele + Frederiksberg Municipality).
* **Interactive B2B Dashboard:** Visual interface with an interactive geospatial map and comparative analytics charts.
* **Real-time 'What-If' Simulation:** Dynamic recalculation of scores based on custom weights (Supply, Demographics, Market Gap).
* **District Deep-Dive:** Comprehensive inspector showing Gen Z demographics, income data, and waste supply metrics against metro averages.
* **Data Export:** Instant CSV report generation for offline B2B reporting.
* **Automated Testing Suite:** Full test coverage with `pytest` for math verification and API stability.

---

## 🧮 The Circular Potential Index (CPI)
The core metric is computed as a weighted combination of three normalized indicators:

$$\text{CPI} = (\text{Supply} \times w_1) + (\text{Demographics} \times w_2) + (\text{Market Gap} \times w_3)$$

* **Supply Score ($w_1 = 0.40$):** Textile waste volume and recycling collection availability.
* **Demographics Score ($w_2 = 0.35$):** Gen Z population density (60%) and average annual income (40%).
* **Market Gap Score ($w_3 = 0.25$):** Relative under-saturation of second-hand and circular fashion stores.

---

## 🛠️ Tech Stack
* **Language:** Python 3.11
* **Backend:** FastAPI, Pydantic v2
* **Frontend:** Streamlit, Plotly
* **Database:** Supabase (PostgreSQL)
* **Testing:** Pytest
* **DevOps:** Docker, Docker Compose, GitHub Actions (CI/CD)

---

## 🚀 Getting Started

### Prerequisites
* Python 3.11+ or Docker Installed

### Option 1: Docker Compose (Recommended)
```bash
git clone [https://github.com/robertomartinengo/copenhagen-recommerce-matrix.git](https://github.com/robertomartinengo/copenhagen-recommerce-matrix.git)
cd copenhagen-recommerce-matrix

docker-compose up --build