import os
import pytest
from pdf_generator import generate_district_pdf


def test_generate_district_pdf_success(tmp_path):
    sample_district = {
        "name": "Nørrebro",
        "cpi_score": 8.9,
        "rank": 1,
        "waste_supply_score": 9.5,
        "demographics_score": 8.3,
        "market_gap_score": 8.8,
        "population_gen_z": 14200,
        "avg_income_dkk": 290000
    }
    
    output_file = os.path.join(tmp_path, "test_report.pdf")
    generated_path = generate_district_pdf(sample_district, filename=output_file)
    
    assert os.path.exists(generated_path)
    assert os.path.getsize(generated_path) > 0