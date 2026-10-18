# ♻️ Copenhagen Re-Commerce Matrix

B2B Location Intelligence Platform for Circular Fashion & Textile Recycling in Greater Copenhagen.

## 🏗️ System Architecture

- **Backend API:** FastAPI with Supabase (PostgreSQL)
- **Control Room:** Streamlit Dashboard with GeoJSON Choropleth Heatmaps & B2B Benchmarking
- **Consumer Interface:** Freemium Telegram Bot
- **Deliverable Engine:** Automated Executive PDF Generator (`fpdf2`)
- **CI/CD:** GitHub Actions with `mypy` static typing and `pytest-cov` test coverage

## 🚀 Quick Start (Docker)

```bash
# Clone the repository
git clone [https://github.com/your-username/Copenhagen_Matrix.git](https://github.com/your-username/Copenhagen_Matrix.git)
cd Copenhagen_Matrix

# Setup environment variables
cp .env.example .env

# Run all containers (API, Dashboard, Telegram Bot)
docker-compose up --build