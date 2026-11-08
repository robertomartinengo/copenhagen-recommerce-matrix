import pytest
from fastapi.testclient import TestClient

import main
from main import app
from cpi_engine import BUSINESS_PROFILES, calculate_dynamic_cpi

# Niente "with TestClient(app)": cosi' il lifespan (bot Telegram) non parte nei test.
client = TestClient(app)


# ---------------------------------------------------------
# 1. UNIT TESTS: cpi_engine
# ---------------------------------------------------------

ZONE = {"waste_supply_score": 8.0, "demographics_score": 6.0, "market_gap_score": 4.0}


@pytest.mark.parametrize("profile", list(BUSINESS_PROFILES))
def test_profile_weights_sum_to_one(profile):
    weights = BUSINESS_PROFILES[profile]["weights"]
    assert sum(weights.values()) == pytest.approx(1.0)


@pytest.mark.parametrize(
    "profile, expected",
    [
        ("vintage_premium", 5.6),   # 8*0.2 + 6*0.4 + 4*0.4
        ("kilo_sale", 6.6),         # 8*0.5 + 6*0.3 + 4*0.2
        ("upcycling", 6.0),         # 8*0.4 + 6*0.2 + 4*0.4
        ("curated_vintage", 5.98),  # 8*0.33 + 6*0.33 + 4*0.34
    ],
)
def test_dynamic_cpi_per_profile(profile, expected):
    result = calculate_dynamic_cpi(ZONE, business_type=profile)
    assert result["cpi_score"] == pytest.approx(expected, abs=0.01)
    assert result["business_profile_used"] == profile
    assert result["business_profile_label"] == BUSINESS_PROFILES[profile]["label"]


def test_unknown_profile_falls_back_to_curated_vintage():
    unknown = calculate_dynamic_cpi(ZONE, business_type="non_esiste")
    curated = calculate_dynamic_cpi(ZONE, business_type="curated_vintage")
    assert unknown["cpi_score"] == curated["cpi_score"]


def test_missing_scores_default_to_five():
    result = calculate_dynamic_cpi({}, business_type="kilo_sale")
    assert result["cpi_score"] == pytest.approx(5.0)


def test_demographics_falls_back_to_cpi_score():
    zone = {"waste_supply_score": 5.0, "market_gap_score": 5.0, "cpi_score": 9.0}
    result = calculate_dynamic_cpi(zone, business_type="vintage_premium")
    # 5*0.2 + 9*0.4 + 5*0.4 = 6.6
    assert result["cpi_score"] == pytest.approx(6.6, abs=0.01)



# ---------------------------------------------------------
# 2. API TESTS: Supabase sostituito da dati finti
# ---------------------------------------------------------

FAKE_ZONES = [
    {"name": "Zona A", "waste_supply_score": 10, "demographics_score": 1, "market_gap_score": 1},
    {"name": "Zona B", "waste_supply_score": 2, "demographics_score": 8, "market_gap_score": 8},
]


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, data):
        self._data = data

    def select(self, *_args, **_kwargs):
        return self

    def execute(self):
        return FakeResponse(self._data)


class FakeSupabase:
    def __init__(self, data):
        self._data = data

    def table(self, _name):
        return FakeQuery(self._data)


@pytest.fixture
def fake_db(monkeypatch):
    monkeypatch.setattr(main, "supabase", FakeSupabase(FAKE_ZONES))


def test_read_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_zones_sorted_by_cpi_descending(fake_db):
    response = client.get("/zones", params={"business_type": "vintage_premium"})
    assert response.status_code == 200
    zones = response.json()
    scores = [z["cpi_score"] for z in zones]
    assert scores == sorted(scores, reverse=True)
    assert all(z["business_profile_used"] == "vintage_premium" for z in zones)


def test_business_type_changes_ranking(fake_db):
    vintage = client.get("/zones", params={"business_type": "vintage_premium"}).json()
    kilo = client.get("/zones", params={"business_type": "kilo_sale"}).json()
    assert vintage[0]["name"] == "Zona B"  # 6.8 contro 2.8
    assert kilo[0]["name"] == "Zona A"     # 5.5 contro 5.0


def test_top_zone_endpoint(fake_db):
    response = client.get("/zones/top", params={"business_type": "kilo_sale"})
    assert response.status_code == 200
    assert response.json()["name"] == "Zona A"


def test_top_zone_empty_returns_empty_dict(monkeypatch):
    monkeypatch.setattr(main, "supabase", FakeSupabase([]))
    response = client.get("/zones/top")
    assert response.status_code == 200
    assert response.json() == {}

