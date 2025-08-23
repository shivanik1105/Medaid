# report_generator.py
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime

def generate_pdf_report(user_profile, session_data):
    """
    Generates a PDF summary of the consultation session.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(name='Title', fontSize=24, alignment=TA_CENTER, spaceAfter=20)
    header_style = ParagraphStyle(name='Header', fontSize=14, alignment=TA_LEFT, spaceAfter=10, fontName='Helvetica-Bold')
    body_style = styles['BodyText']
    
    story = []
    
    # --- Title ---
    story.append(Paragraph("AI Health Triage Summary", title_style))
    story.append(Spacer(1, 0.25 * 72)) # 0.25 inch space

    # --- User Details ---
    story.append(Paragraph("Patient Information", header_style))
    user_details = [
        ["Name:", user_profile.get('name', 'N/A')],
        ["Age:", str(user_profile.get('age', 'N/A'))],
        ["Date:", datetime.now().strftime("%Y-%m-%d %H:%M")]
    ]
    user_table = Table(user_details, colWidths=[1.5*72, 4*72])
    user_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(user_table)
    story.append(Spacer(1, 0.25 * 72))

    # --- Triage Results ---
    triage_result = session_data.get('triage_result', {})
    story.append(Paragraph("Triage Assessment", header_style))
    risk_level = triage_result.get('risk_level', 'N/A')
    
    # Color code the risk level
    if "High" in risk_level:
        risk_color = colors.HexColor("#ff4b4b") # Streamlit's error color
    elif "Moderate" in risk_level:
        risk_color = colors.HexColor("#ffc400") # Streamlit's warning color
    else:
        risk_color = colors.HexColor("#2e9a6f") # Streamlit's success color

    risk_style = ParagraphStyle(name='Risk', fontSize=12, alignment=TA_LEFT, textColor=risk_color, fontName='Helvetica-Bold')

    triage_details = [
        [Paragraph("<b>Overall Risk Level:</b>", body_style), Paragraph(risk_level, risk_style)],
        [Paragraph("<b>Confidence:</b>", body_style), Paragraph(f"{triage_result.get('confidence', 0)*100:.0f}%", body_style)],
        [Paragraph("<b>AI Reasoning:</b>", body_style), Paragraph(triage_result.get('reason', 'N/A'), body_style)],
    ]
    triage_table = Table(triage_details, colWidths=[1.5*72, 4*72])
    triage_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(triage_table)
    story.append(Spacer(1, 0.25 * 72))

    # --- User Provided Information ---
    story.append(Paragraph("Information Provided by User", header_style))
    info_details = [
        ["Current Symptoms:", session_data.get('current_symptoms_text', 'N/A')],
        ["Past History:", ", ".join(session_data.get('past_history', ['N/A']))],
        ["Report Data:", str(session_data.get('report_data', 'No report uploaded'))],
    ]
    info_table = Table(info_details, colWidths=[1.5*72, 4*72])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(info_table)

    doc.build(story)
    
    buffer.seek(0)
    return buffer.getvalue()
