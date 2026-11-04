import os

from google import genai
from google.genai import types

# Modello configurabile da variabile d'ambiente (es. su Render) senza toccare il codice.
DEFAULT_MODEL = "gemini-3.7-flash"

_client = None


def _get_client():
    """Crea il client Gemini al primo uso. Restituisce None se manca la chiave.

    La chiave viene letta qui (e non all'import) cosi' funziona anche se
    load_dotenv() viene eseguito dopo l'import di questo modulo.
    """
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            _client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(timeout=20000),  # millisecondi
            )
    return _client


def generate_executive_narrative(zone_data: dict, business_type: str = "curated_vintage") -> str:
    """
    Genera un'analisi executive su misura usando Gemini API.
    Se la chiave manca o l'API non risponde, attiva un fallback elegante senza interrompere il servizio.
    """
    name = zone_data.get("name", "N/A")
    cpi = zone_data.get("cpi_score", 0)
    gen_z = zone_data.get("population_gen_z", 0)
    avg_income = zone_data.get("avg_income_dkk", 0)
    business_label = zone_data.get("business_profile_label", business_type)

    client = _get_client()
    if client is None:
        return _fallback_narrative(name, cpi, gen_z, avg_income, business_label)

    prompt = f"""
Sei un Senior Real Estate & Retail Analyst specializzato in Re-Commerce e moda circolare a Copenhagen.
Scrivi una brevissima analisi di mercato strategica (massimo 70 parole, 3 righe fluide e dense) per un investitore B2B.

Dati Location:
- Distretto: {name}
- Modello Business Richiesto: {business_label}
- Indice Potenziale (CPI): {cpi}/10
- Target Gen Z: {gen_z:,.0f} residenti
- Reddito Medio: {avg_income:,.0f} DKK

Requisiti del testo:
1. Tono executive, analitico e professionale.
2. Spiega perche la combinazione di questi dati favorisce o penalizza il modello "{business_label}".
3. Sii sintetico e diretto, senza convenevoli. Zero elenchi puntati, solo testo fluido.
"""

    try:
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", DEFAULT_MODEL),
            contents=prompt,
            config=types.GenerateContentConfig(
                # Margine ampio: nei modelli recenti anche il "ragionamento" interno
                # consuma token e un limite troppo basso puo' dare risposte vuote.
                # La lunghezza del testo e' controllata dal prompt (max 70 parole).
                max_output_tokens=1024,
                temperature=0.4,
            ),
        )
        text = getattr(response, "text", None)
        if text and text.strip():
            return text.strip()
        print("⚠️ [AI REPORTER] Risposta vuota dal modello, uso il fallback.")
    except Exception as e:
        print(f"⚠️ [AI REPORTER] Fallback attivato a causa di: {e}")

    return _fallback_narrative(name, cpi, gen_z, avg_income, business_label)


def _fallback_narrative(name: str, cpi: float, gen_z: int, avg_income: float, business_label: str) -> str:
    """Fallback deterministico professionale se l'API non risponde."""
    cpi_val = float(cpi)
    if cpi_val >= 8.0:
        return (
            f"Il distretto di {name} presenta un'eccellente sinergia per il format {business_label}. "
            f"L'elevata concentrazione di target Gen Z ({gen_z:,.0f} residenti) e le condizioni di mercato "
            f"locali garantiscono un rapido assorbimento dell'offerta e un posizionamento ad alto ROI."
        )
    elif cpi_val >= 7.0:
        return (
            f"{name} offre un contesto favorevole per lo sviluppo di {business_label}. "
            f"Con un reddito medio di {avg_income/1000:,.0f}k DKK e un volume solido di clientela giovane, "
            f"si consiglia una penetrazione di mercato tramite boutique fisiche flessibili o pop-up."
        )
    else:
        return (
            f"Il profilo di {name} mostra una priorita secondaria per {business_label}. "
            f"L'indice CPI di {cpi_val:.1f} suggerisce un approccio prudente, preferendo "
            f"test di mercato digitali o collaborazioni locali prima di impegnare capitale in retail fisico."
        )