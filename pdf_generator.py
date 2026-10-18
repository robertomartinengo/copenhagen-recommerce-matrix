import os
from fpdf import FPDF


class ExecutivePDFReport(FPDF):
    def header(self) -> None:
        self.set_font('helvetica', 'B', 16)
        self.set_text_color(33, 37, 41)
        self.cell(0, 10, 'Copenhagen Re-Commerce Matrix', ln=1, align='L')
        self.set_font('helvetica', 'I', 10)
        self.set_text_color(108, 117, 125)
        self.cell(0, 6, 'B2B Location Intelligence Executive Report', ln=1, align='L')
        self.line(10, 25, 200, 25)
        self.ln(10)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(108, 117, 125)
        self.cell(0, 10, f'Page {self.page_no()} | Generated for Circular Economy Retail Analytics', align='C')


def generate_district_pdf(district_data: dict, filename: str = "executive_report.pdf") -> str:
    pdf = ExecutivePDFReport()
    pdf.add_page()
    
    district_name = district_data.get('name', 'Unknown District')
    cpi_score = district_data.get('cpi_score', 0.0)
    rank = district_data.get('rank', 'N/A')
    
    # Intestazione Distretto
    pdf.set_font('helvetica', 'B', 14)
    pdf.set_text_color(13, 110, 253)
    pdf.cell(0, 10, f"District Strategic Summary: {district_name}", ln=1, align='L')
    pdf.ln(4)
    
    # Punteggi Principali
    pdf.set_font('helvetica', 'B', 11)
    pdf.set_text_color(33, 37, 41)
    pdf.cell(0, 8, "Core Assessment Metrics:", ln=1, align='L')
    
    pdf.set_font('helvetica', '', 10)
    pdf.cell(0, 7, f"- Circular Potential Index (CPI): {cpi_score:.1f} / 10", ln=1)
    pdf.cell(0, 7, f"- Metropolitan Ranking: #{rank}", ln=1)
    pdf.ln(4)
    
    # Breakdown Componenti
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(0, 8, "Key Pillar Breakdown:", ln=1, align='L')
    pdf.set_font('helvetica', '', 10)
    
    supply = district_data.get('waste_supply_score', district_data.get('supply_score', 0.0))
    demo = district_data.get('demographics_score', 0.0)
    gap = district_data.get('market_gap_score', 0.0)
    
    pdf.cell(0, 7, f"- Textile Waste Supply Score: {supply:.1f} / 10", ln=1)
    pdf.cell(0, 7, f"- Demographics & Target Score: {demo:.1f} / 10", ln=1)
    pdf.cell(0, 7, f"- Market Opportunity Gap Score: {gap:.1f} / 10", ln=1)
    pdf.ln(4)
    
    # Indicatori socio-demografici
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(0, 8, "Socio-Demographic Indicators:", ln=1, align='L')
    pdf.set_font('helvetica', '', 10)
    
    gen_z = district_data.get('population_gen_z', district_data.get('gen_z_percentage', 0))
    income = district_data.get('avg_income_dkk', district_data.get('avg_annual_income_eur', 0))
    
    gen_z_str = f"{gen_z:,.0f} residents" if gen_z > 100 else f"{gen_z:.1f}%"
    pdf.cell(0, 7, f"- Gen Z Target Density: {gen_z_str}", ln=1)
    pdf.cell(0, 7, f"- Average Income Level: {income:,.0f} DKK", ln=1)
    pdf.ln(6)
    
    # Raccomandazione per il Commerciante
    pdf.set_font('helvetica', 'B', 11)
    pdf.set_text_color(13, 110, 253)
    pdf.cell(0, 8, "Retail Expansion Insight:", ln=1, align='L')
    pdf.set_font('helvetica', '', 10)
    pdf.set_text_color(33, 37, 41)
    
    recommendation = (
        f"{district_name} achieves a Circular Potential Index of {cpi_score:.1f}. "
        f"The district features strong material supply availability paired with favorable "
        f"demographic conditions, making it an ideal strategic choice for opening a new circular retail outlet, "
        f"second-hand boutique, or recycling collection point."
    )
    pdf.multi_cell(0, 6, recommendation)
    
    pdf.output(filename)
    return filename