import ai_reporter

ZONE = {
    "name": "Vesterbro",
    "cpi_score": 8.4,
    "population_gen_z": 12000,
    "avg_income_dkk": 310000,
    "business_profile_label": "Boutique / Lusso",
}


class FakeResponse:
    def __init__(self, text):
        self.text = text


class FakeModels:
    def __init__(self, text=None, error=None):
        self._text, self._error, self.calls = text, error, []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self._error:
            raise self._error
        return FakeResponse(self._text)


class FakeClient:
    def __init__(self, **kwargs):
        self.models = FakeModels(**kwargs)


def test_fallback_when_no_client(monkeypatch):
    monkeypatch.setattr(ai_reporter, "_get_client", lambda: None)
    text = ai_reporter.generate_executive_narrative(ZONE)
    assert "Vesterbro" in text and "eccellente sinergia" in text


def test_uses_model_text_and_strips(monkeypatch):
    client = FakeClient(text="  Analisi AI.  ")
    monkeypatch.setattr(ai_reporter, "_get_client", lambda: client)
    monkeypatch.setenv("GEMINI_MODEL", "modello-di-prova")
    assert ai_reporter.generate_executive_narrative(ZONE) == "Analisi AI."
    assert client.models.calls[0]["model"] == "modello-di-prova"


def test_fallback_on_api_error(monkeypatch):
    client = FakeClient(error=RuntimeError("quota"))
    monkeypatch.setattr(ai_reporter, "_get_client", lambda: client)
    assert "Vesterbro" in ai_reporter.generate_executive_narrative(ZONE)


def test_fallback_on_empty_response(monkeypatch):
    client = FakeClient(text="   ")
    monkeypatch.setattr(ai_reporter, "_get_client", lambda: client)
    assert "Vesterbro" in ai_reporter.generate_executive_narrative(ZONE)


def test_get_client_none_without_key(monkeypatch):
    monkeypatch.setattr(ai_reporter, "_client", None)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert ai_reporter._get_client() is None
