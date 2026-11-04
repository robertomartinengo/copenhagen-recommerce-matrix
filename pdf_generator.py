import os
from fpdf import FPDF
from typing import Tuple
from ai_reporter import generate_executive_narrative

class B2BExecutivePDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()
        
        # Sfondo Bianco Puro (A4 = 210 x 297 mm)
        self.set_fill_color(255, 255, 255)
        self.rect(0, 0, 210, 297, style="F")

    def rounded_rect(self, x, y, w, h, r, style=""):
        """Disegna un rettangolo con angoli arrotondati calcolati."""
        k = self.k
        hp = self.h
        if style == "F":
            op = "f"
        elif style == "FD" or style == "DF":
            op = "B"
        else:
            op = "S"
            
        MyArc = 4/3 * (2**0.5 - 1)
        
        self._out(f"{x * k:.2f} {(hp - y - r) * k:.2f} m")
        
        xc = x + r
        yc = y + r
        self._out(f"{x * k:.2f} {(hp - yc + r * MyArc) * k:.2f} {(xc - r * MyArc) * k:.2f} {(hp - y) * k:.2f} {xc * k:.2f} {(hp - y) * k:.2f} c")
        
        xc = x + w - r
        self._out(f"{xc * k:.2f} {(hp - y) * k:.2f} l")
        self._out(f"{(xc + r * MyArc) * k:.2f} {(hp - y) * k:.2f} {(x + w) * k:.2f} {(hp - yc + r * MyArc) * k:.2f} {(x + w) * k:.2f} {(hp - yc) * k:.2f} c")
        
        yc = y + h - r
        self._out(f"{(x + w) * k:.2f} {(hp - yc) * k:.2f} l")
        self._out(f"{(x + w) * k:.2f} {(hp - yc - r * MyArc) * k:.2f} {(xc + r * MyArc) * k:.2f} {(hp - y - h) * k:.2f} {xc * k:.2f} {(hp - y - h) * k:.2f} c")
        
        xc = x + r
        self._out(f"{xc * k:.2f} {(hp - y - h) * k:.2f} l")
        self._out(f"{(xc - r * MyArc) * k:.2f} {(hp - y - h) * k:.2f} {x * k:.2f} {(hp - yc - r * MyArc) * k:.2f} {x * k:.2f} {(hp - yc) * k:.2f} c")
        
        self._out(f"{x * k:.2f} {(hp - yc) * k:.2f} l")
        self._out(op)

    def draw_progress_bar(self, x, y, width, height, progress_score, bg_color: Tuple[int, int, int], fill_color: Tuple[int, int, int]):
        """Disegna una barra di progresso orizzontale arrotondata."""
        self.set_fill_color(*bg_color)
        self.set_draw_color(*bg_color)
        self.rounded_rect(x, y, width, height, r=height/2, style="F")
        
        fill_width = max(height, (progress_score / 10.0) * width)
        self.set_fill_color(*fill_color)
        self.set_draw_color(*fill_color)
        self.rounded_rect(x, y, fill_width, height, r=height/2, style="F")

def generate_executive_pdf(zone_data: dict, filename: str = "Executive_Report_Design.pdf"):
    pdf = B2BExecutivePDF()
    
    # Palette Colori Executive & Salvia
    COLOR_SALVIA = (110, 142, 128)      
    COLOR_SALVIA_LIGHT = (235, 240, 237) 
    COLOR_DARK = (31, 41, 55)           
    COLOR_GRAY = (107, 114, 128)        
    COLOR_BAR_BG = (243, 244, 246)      
    
    # Dati zona
    name = zone_data.get("name", "N/A").upper()
    cpi = float(zone_data.get("cpi_score", 0))
    gen_z = zone_data.get("population_gen_z", 0)
    avg_income = zone_data.get("avg_income_dkk", 0)
    waste_score = float(zone_data.get("waste_supply_score", 0))
    demo_score = float(zone_data.get("demographics_score", zone_data.get("cpi_score", 0)))
    gap_score = float(zone_data.get("market_gap_score", 0))

    # --- INTESTAZIONE ---
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*COLOR_GRAY)
    pdf.set_xy(20, 20)
    pdf.cell(0, 5, "COPENHAGEN RE-COMMERCE MATRIX")
    
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*COLOR_DARK)
    pdf.set_xy(20, 28)
    pdf.cell(0, 10, name)
    
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*COLOR_GRAY)
    pdf.set_xy(20, 39)
    pdf.cell(0, 5, "Executive Summary & Market Potential Analysis")
    
    pdf.set_draw_color(*COLOR_SALVIA)
    pdf.set_line_width(0.8)
    pdf.line(20, 48, 190, 48)

    # --- KPI HERO SECTION ---
    y_kpi = 58
    card_width = 54
    card_height = 35
    margin_x = 20
    spacing = 4
    
    # Card 1: CPI
    x_cpi = margin_x
    pdf.set_fill_color(*COLOR_SALVIA_LIGHT)
    pdf.set_draw_color(*COLOR_SALVIA_LIGHT)
    pdf.rounded_rect(x_cpi, y_kpi, card_width, card_height, r=4, style="F")
    
    pdf.set_xy(x_cpi, y_kpi + 6)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*COLOR_GRAY)
    pdf.cell(card_width, 5, "INDICE CPI", align="C")
    
    pdf.set_xy(x_cpi, y_kpi + 14)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(*COLOR_SALVIA)
    pdf.cell(card_width, 10, f"{cpi:.1f}", align="C")
    
    pdf.set_xy(x_cpi, y_kpi + 23)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*COLOR_GRAY)
    pdf.cell(card_width, 5, "Punteggio su 10", align="C")

    # Card 2: GEN Z
    x_genz = x_cpi + card_width + spacing
    pdf.set_fill_color(*COLOR_SALVIA_LIGHT)
    pdf.rounded_rect(x_genz, y_kpi, card_width, card_height, r=4, style="F")
    
    pdf.set_xy(x_genz, y_kpi + 6)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*COLOR_GRAY)
    pdf.cell(card_width, 5, "TARGET GEN Z", align="C")
    
    pdf.set_xy(x_genz, y_kpi + 15)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*COLOR_DARK)
    pdf.cell(card_width, 8, f"{gen_z:,.0f}", align="C")
    
    pdf.set_xy(x_genz, y_kpi + 23)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*COLOR_GRAY)
    pdf.cell(card_width, 5, "Residenti core", align="C")

    # Card 3: REDDITO
    x_income = x_genz + card_width + spacing
    pdf.set_fill_color(*COLOR_SALVIA_LIGHT)
    pdf.rounded_rect(x_income, y_kpi, card_width, card_height, r=4, style="F")
    
    pdf.set_xy(x_income, y_kpi + 6)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*COLOR_GRAY)
    pdf.cell(card_width, 5, "REDDITO MEDIO", align="C")
    
    pdf.set_xy(x_income, y_kpi + 15)
    pdf.set_font("Helvetica", "B", 17)
    pdf.set_text_color(*COLOR_DARK)
    pdf.cell(card_width, 8, f"{avg_income/1000:,.0f}k DKK", align="C")
    
    pdf.set_xy(x_income, y_kpi + 23)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*COLOR_GRAY)
    pdf.cell(card_width, 5, "Pro-capite annuo", align="C")

    # --- GRAFICI SCORE ---
    y_scores = 105
    pdf.set_xy(20, y_scores)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*COLOR_DARK)
    pdf.cell(0, 8, "Indicatori Strategici di Mercato")
    
    metrics = [
        ("Materiale Tessile Usato e Waste Supply", waste_score),
        ("Concentrazione Demografica (Youngs / Gen Z)", demo_score),
        ("Saturazione e Opportunita di Gap Retail", gap_score),
    ]

    y_bar = y_scores + 12
    for label, score in metrics:
        pdf.set_xy(20, y_bar)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*COLOR_DARK)
        pdf.cell(100, 6, label)
        
        pdf.set_xy(160, y_bar)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*COLOR_SALVIA)
        pdf.cell(30, 6, f"{score:.1f} / 10", align="R")
        
        pdf.draw_progress_bar(x=20, y=y_bar + 7, width=170, height=5, progress_score=score, bg_color=COLOR_BAR_BG, fill_color=COLOR_SALVIA)
        
        y_bar += 18

    # --- RACCOMANDAZIONE DALL'AI NARRATIVE ENGINE ---
    y_rec = y_bar + 10
    
    rec_text = generate_executive_narrative(
        zone_data, 
        business_type=zone_data.get("business_profile_used", "curated_vintage")
    )
    rec_title = f"Analisi Strategica B2B — {zone_data.get('business_profile_label', 'Re-Commerce')}"

    pdf.set_fill_color(*COLOR_SALVIA_LIGHT)
    pdf.rounded_rect(20, y_rec, 170, 42, r=4, style="F")
    
    pdf.set_xy(25, y_rec + 5)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*COLOR_SALVIA)
    pdf.cell(0, 5, rec_title.upper())
    
    pdf.set_xy(25, y_rec + 12)
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(*COLOR_DARK)
    pdf.multi_cell(160, 4.8, rec_text)

    # --- FOOTER ---
    pdf.set_xy(20, 275)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(156, 163, 175)
    pdf.cell(0, 5, "Copenhagen Re-Commerce Matrix  |  Generato tramite AI")
    pdf.set_xy(160, 275)
    pdf.cell(30, 5, "Pagina 1 di 1", align="R")

    pdf.output(filename)
    return filename