import ai_reporter

ZONE = {
    "name": "Vesterbro",
    "cpi_score": 8.4,
    "population_gen_z": 12000,
    "avg_income_dkk": 310000,
    "business_profile_label": "Boutique / Lusso",
}


def test_fallback_when_no_llm_response(monkeypatch):
    monkeypatch.setattr(ai_reporter, "call_llm_with_fallback", lambda prompt: None)
    text = ai_reporter.generate_executive_narrative(ZONE)
    assert "Vesterbro" in text and "eccellente sinergia" in text


def test_uses_llm_text_and_strips(monkeypatch):
    monkeypatch.setattr(ai_reporter, "call_llm_with_fallback", lambda prompt: "  Analisi AI.  ")
    assert ai_reporter.generate_executive_narrative(ZONE) == "Analisi AI."


def test_fallback_on_api_error(monkeypatch):
    def _raises(prompt):
        raise RuntimeError("quota")
    monkeypatch.setattr(ai_reporter, "call_llm_with_fallback", _raises)
    assert "Vesterbro" in ai_reporter.generate_executive_narrative(ZONE)


def test_fallback_on_empty_response(monkeypatch):
    monkeypatch.setattr(ai_reporter, "call_llm_with_fallback", lambda prompt: "   ")
    assert "Vesterbro" in ai_reporter.generate_executive_narrative(ZONE)
