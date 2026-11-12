from autorouting import call_llm_with_fallback

# Modello configurabile da variabile d'ambiente (es. su Render) senza toccare il codice.
DEFAULT_MODEL = "gemini-3.8-flash"


def generate_executive_narrative(zone_data: dict, business_type: str = "curated_vintage") -> str:
    """Genera un'analisi executive (testo LLM o fallback deterministico)."""
    text, _source = generate_executive_narrative_with_source(zone_data, business_type)
    return text


def generate_executive_narrative_with_source(
    zone_data: dict, business_type: str = "curated_vintage"
) -> tuple[str, str]:
    """Genera l'analisi executive restituendo la tupla (testo, sorgente).

    sorgente puo essere 'llm' (risposta da provider AI) oppure 'template'
    (fallback deterministico se l'API fallisce o e disabilitata).
    Il footer del PDF la usa per dichiarare in modo onesto l'origine del testo.
    """
    name = zone_data.get("name", "N/A")
    cpi = zone_data.get("cpi_score", 0)
    gen_z = zone_data.get("population_gen_z", 0)
    avg_income = zone_data.get("avg_income_dkk", 0)
    business_label = zone_data.get("business_profile_label", business_type)

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
        text = call_llm_with_fallback(prompt)
    except Exception:
        text = None
    if text and text.strip():
        return text.strip(), "llm"

    return _fallback_narrative(name, cpi, gen_z, avg_income, business_label), "template"


def _fallback_narrative(name: str, cpi: float, gen_z: int, avg_income: float, business_label: str) -> str:
    """Fallback deterministico professionale se l'API non risponde."""
    cpi_val = float(cpi)
    if cpi_val >= 8.0:
        return (
            f"Il distretto di {name} presenta un'eccellente sinergia per il format {business_label}. "
            f"L'elevata concentrazione di target Gen Z ({gen_z:,.0f} residenti) e le condizioni di mercato "
            f"locali favoriscono lo sviluppo di un punto vendita di prossimita."
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