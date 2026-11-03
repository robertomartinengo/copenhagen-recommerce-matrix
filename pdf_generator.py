from datetime import datetime
from fpdf import FPDF


class B2BExecutivePDF(FPDF):
    def header(self):
        # Banner Superiore
        self.set_fill_color(30, 41, 59)  # Deep Navy (#1E293B)
        self.rect(0, 0, 210, 18, "F")

        self.set_font("Helvetica", "B", 10)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 4)
        self.cell(100, 10, "COPENHAGEN RE-COMMERCE MATRIX", ln=False)

        self.set_font("Helvetica", "", 9)
        self.cell(90, 10, "CONFIDENTIAL & PROPRIETARY B2B REPORT", align="R", ln=True)

        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 116, 139)  # Slate Grey
        self.cell(0, 10, f"Pagina {self.page_no()} | Generato il {datetime.now().strftime('%d/%m/%Y %H:%M')}", align="C")


def generate_district_pdf(district_data: dict, filename: str = "District_Report.pdf"):
    pdf = B2BExecutivePDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Mappatura sicura dei campi
    district_name = district_data.get("name", "Distretto Sconosciuto")
    cpi_score = district_data.get("cpi_score", 0.0)
    supply_score = district_data.get("waste_supply_score", district_data.get("supply_score", 0.0))
    demo_score = district_data.get("demographics_score", district_data.get("demo_score", 0.0))
    gap_score = district_data.get("market_gap_score", district_data.get("gap_score", 0.0))

    gen_z = district_data.get("population_gen_z", district_data.get("gen_z_percentage", "N/A"))
    if isinstance(gen_z, (int, float)):
        gen_z_str = f"{gen_z:,.0f} ab." if gen_z > 100 else f"{gen_z:.1f}%"
    else:
        gen_z_str = str(gen_z)

    income = district_data.get("avg_income_dkk", district_data.get("avg_annual_income_eur", None))
    income_str = f"{income:,.0f} DKK" if income else "N/A"

    # ---------------------------------------------------------
    # 1. TITOLO E SOTTO-TITOLO
    # ---------------------------------------------------------
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(15, 23, 42)  # Dark Navy (#0F172A)
    pdf.cell(0, 12, f"Analisi Strategica: {district_name}", ln=True)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 6, f"Scheda Valutazione di Fattibilita per Apertura Store & Hub Circolare", ln=True)
    pdf.ln(6)

    # ---------------------------------------------------------
    # 2. EXECUTIVE KPI CARDS (BOX 2x2)
    # ---------------------------------------------------------
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 8, "1. Key Performance Indicators (KPI)", ln=True)
    pdf.ln(2)

    # Card CPI Main Score
    pdf.set_fill_color(241, 245, 249)  # Light Slate (#F1F5F9)
    pdf.rect(10, 52, 90, 22, "F")
    pdf.set_xy(12, 54)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(86, 4, "CIRCULAR POTENTIAL INDEX (CPI)", ln=True)
    pdf.set_x(12)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(14, 116, 144)  # Cyan/Teal (#0E7490)
    pdf.cell(86, 10, f"{cpi_score:.1f} / 10.0", ln=True)

    # Card Target Gen Z
    pdf.rect(110, 52, 90, 22, "F")
    pdf.set_xy(112, 54)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(86, 4, "BACINO TARGET GEN Z", ln=True)
    pdf.set_x(112)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(86, 10, gen_z_str, ln=True)

    # Card Supply Score
    pdf.rect(10, 78, 90, 22, "F")
    pdf.set_xy(12, 80)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(86, 4, "DISPONIBILITA MATERIA PRIMA (SUPPLY)", ln=True)
    pdf.set_x(12)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(86, 10, f"{supply_score:.1f} / 10.0", ln=True)

    # Card Market Gap
    pdf.rect(110, 78, 90, 22, "F")
    pdf.set_xy(112, 80)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(86, 4, "OPPORTUNITA DI MERCATO (GAP)", ln=True)
    pdf.set_x(112)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(86, 10, f"{gap_score:.1f} / 10.0", ln=True)

    pdf.set_y(106)
    pdf.ln(4)

    # ---------------------------------------------------------
    # 3. POSIZIONAMENTO E ANALISI "OCEANO BLU"
    # ---------------------------------------------------------
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 8, "2. Posizionamento Strategico & Matrice Oceano Blu", ln=True)

    # Determinazione Quadrante
    if supply_score >= 7.0 and gap_score >= 7.0:
        quadrant_status = "Oceano Blu (Tier 1 - Primario)"
        quadrant_desc = (
            f"{district_name} si colloca nel quadrante ideale 'Oceano Blu'. Unisce un elevato "
            f"volume di scarti/raccolta tessile con una presenza limitata di competitor diretti. "
            f"Rappresenta la scelta prioritaria per investimenti ad alto rendimento."
        )
    elif supply_score >= 7.0 and gap_score < 7.0:
        quadrant_status = "Area ad Alta Densita (Elevata Competizione)"
        quadrant_desc = (
            f"{district_name} presenta un'ottima disponibilita di materia prima ma soffre di "
            f"un'elevata concentrazione di competitor. Consigliato per store con forte differenziazione di brand."
        )
    elif supply_score < 7.0 and gap_score >= 7.0:
        quadrant_status = "Mercato Emergente (Sviluppo Futuro)"
        quadrant_desc = (
            f"{district_name} mostra un ampio gap di mercato non presidiato, ma il bacino di raccolta "
            f"tessile locale e ancora in fase di consolidamento."
        )
    else:
        quadrant_status = "Zona Bassa Priorita (Watchlist)"
        quadrant_desc = (
            f"{district_name} registra punteggi moderati sia nella supply che nell'opportunita di mercato. "
            f"Attualmente sconsigliata come prima apertura flagship."
        )

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(14, 116, 144)
    pdf.cell(0, 6, f"Classificazione: {quadrant_status}", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(51, 65, 85)
    pdf.multi_cell(0, 5, quadrant_desc)
    pdf.ln(6)

    # ---------------------------------------------------------
    # 4. TABELLA DI DETTAGLIO SCORE
    # ---------------------------------------------------------
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 8, "3. Dettaglio Punteggi e Modello di Calcolo", ln=True)
    pdf.ln(2)

    # Intestazione Tabella
    pdf.set_fill_color(30, 41, 59)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(80, 7, "  Pilastro Strategico", border=0, fill=True)
    pdf.cell(35, 7, "Punteggio (0-10)", border=0, fill=True, align="C")
    pdf.cell(35, 7, "Peso Modello", border=0, fill=True, align="C")
    pdf.cell(40, 7, "Valore Assoluto", border=0, fill=True, align="C", ln=True)

    # Righe Tabella
    rows = [
        ("Materia Prima Tessile (Supply)", f"{supply_score:.1f}", "40%", "Volume Tessile"),
        ("Profilo Demografico (Gen Z)", f"{demo_score:.1f}", "35%", gen_z_str),
        ("Opportunita di Mercato (Gap)", f"{gap_score:.1f}", "25%", "Indice Competitor"),
        ("Reddito Medio Annuo", "N/A", "Filtro", income_str)
    ]

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(51, 65, 85)
    fill_row = False

    for name_col, score_col, weight_col, val_col in rows:
        pdf.set_fill_color(248, 250, 252) if fill_row else pdf.set_fill_color(255, 255, 255)
        pdf.cell(80, 7, f"  {name_col}", border=0, fill=True)
        pdf.cell(35, 7, score_col, border=0, fill=True, align="C")
        pdf.cell(35, 7, weight_col, border=0, fill=True, align="C")
        pdf.cell(40, 7, val_col, border=0, fill=True, align="C", ln=True)
        fill_row = not fill_row

    pdf.ln(8)

    # ---------------------------------------------------------
    # 5. RACCOMANDAZIONI OPERATIVE B2B
    # ---------------------------------------------------------
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 8, "4. Raccomandazioni d'Azione per Investitori", ln=True)
    pdf.ln(2)

    recs = [
        ("Format Consigliato: ", "Pop-Up Store o Flagship di Second-Hand ad alto passaggio."),
        ("Strategia Sourcing: ", "Installazione di punti di raccolta direct-to-consumer per intercettare il flusso di materia prima."),
        ("Prossimo Passo: ", "Pianificare un sopralluogo per valutare la disponibilita di locali commerciali liberi nella sotto-zona.")
    ]

    pdf.set_font("Helvetica", "", 9.5)
    for prefix, body in recs:
        pdf.set_text_color(14, 116, 144)
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.write(5, f"- {prefix}")
        pdf.set_text_color(51, 65, 85)
        pdf.set_font("Helvetica", "", 9.5)
        pdf.write(5, f"{body}\n")

    # Salva il file PDF
    pdf.output(filename)
    return filename