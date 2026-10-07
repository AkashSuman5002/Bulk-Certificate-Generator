import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


def render_certificate(
    *, organization_name: str, event_name: str, event_date: date,
    recipient_name: str, certificate_id: str, signatory_name: str,
) -> bytes:
    buffer = io.BytesIO()
    page_width, page_height = landscape(letter)
    pdf = canvas.Canvas(buffer, pagesize=(page_width, page_height))
    pdf.setFillColor(colors.HexColor("#0f2747"))
    pdf.rect(0, 0, page_width, page_height, fill=1, stroke=0)
    pdf.setStrokeColor(colors.HexColor("#d4af37"))
    pdf.setLineWidth(4)
    pdf.rect(0.35 * inch, 0.35 * inch, page_width - 0.7 * inch, page_height - 0.7 * inch, fill=0, stroke=1)
    pdf.setFillColor(colors.HexColor("#d4af37"))
    pdf.setFont("Helvetica-Bold", 27)
    pdf.drawCentredString(page_width / 2, page_height - 1.2 * inch, organization_name.upper())
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 31)
    pdf.drawCentredString(page_width / 2, page_height - 2.05 * inch, "CERTIFICATE OF PARTICIPATION")
    pdf.setFont("Helvetica", 15)
    pdf.drawCentredString(page_width / 2, page_height - 2.65 * inch, "This certificate is proudly presented to")
    pdf.setFillColor(colors.HexColor("#d4af37"))
    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawCentredString(page_width / 2, page_height - 3.35 * inch, recipient_name.upper())
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica", 15)
    pdf.drawCentredString(page_width / 2, page_height - 3.95 * inch, f"for successfully participating in {event_name}")
    pdf.drawCentredString(page_width / 2, page_height - 4.35 * inch, f"held on {event_date.strftime('%B %-d, %Y') if not __import__('sys').platform.startswith('win') else event_date.strftime('%B %#d, %Y')}.")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(0.85 * inch, 0.95 * inch, f"Certificate ID: {certificate_id}")
    pdf.line(page_width - 2.9 * inch, 1.25 * inch, page_width - 0.85 * inch, 1.25 * inch)
    pdf.drawCentredString(page_width - 1.875 * inch, 0.95 * inch, "Authorized Signatory")
    pdf.drawCentredString(page_width - 1.875 * inch, 0.7 * inch, signatory_name)
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()