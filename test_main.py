import pytest
from fastapi.testclient import TestClient
from main import app
from cpi_engine import compute_cpi, calculate_demographics_score

client = TestClient(app)

# ---------------------------------------------------------
# 1. UNIT TESTS (Verifica logica matematica)
# ---------------------------------------------------------

def test_demographics_score_calculation():
    # Test valore massimo
    score = calculate_demographics_score(gen_z_pop=15000, income=450000)
    assert score == 10.0

    # Test valore intermedio
    score_mid = calculate_demographics_score(gen_z_pop=7500, income=225000)
    assert round(score_mid, 1) == 5.0

def test_compute_cpi_baseline():
    # Nørrebro baseline: waste=9.5, gen_z=14200, income=290000, gap=8.8
    # CPI atteso con pesi 0.40, 0.35, 0.25 -> 8.89
    cpi = compute_cpi(9.5, 14200, 290000, 8.8)
    assert cpi == 8.89

def test_compute_cpi_custom_weights():
    # Stessi dati ma con pesi diversi
    cpi_custom = compute_cpi(9.5, 14200, 290000, 8.8, w_supply=0.20, w_demo=0.20, w_gap=0.60)
    assert isinstance(cpi_custom, float)
    assert cpi_custom > 0

# ---------------------------------------------------------
# 2. INTEGRATION TESTS (Verifica endpoint API)
# ---------------------------------------------------------

def test_read_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["supabase_connected"] is True

def test_get_zones_endpoint():
    response = client.get("/zones")
    assert response.status_code == 200
    zones = response.json()
    assert isinstance(zones, list)
    assert len(zones) == 11

def test_get_single_zone_success():
    response = client.get("/zones/DK-2200")
    assert response.status_code == 200
    zone = response.json()
    assert zone["name"] == "Nørrebro"

def test_get_single_zone_not_found():
    response = client.get("/zones/INVALID-CODE")
    assert response.status_code == 404

def test_simulation_valid_weights():
    payload = {
        "weight_supply": 0.20,
        "weight_demographics": 0.20,
        "weight_market_gap": 0.60
    }
    response = client.post("/simulate-cpi", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["results"]) == 11

def test_simulation_invalid_weights_sum():
    # Somma pesi = 0.80 (deve fallire con 400 Bad Request)
    payload = {
        "weight_supply": 0.50,
        "weight_demographics": 0.20,
        "weight_market_gap": 0.10
    }
    response = client.post("/simulate-cpi", json=payload)
    assert response.status_code == 400

def test_export_csv_endpoint():
    response = client.get("/export/csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")