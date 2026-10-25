import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from transactions.models import AuditException, Invoice, Payment, Vendor

def generate_pdf_audit_report():
    """Generates an Executive Audit Exception Report in PDF using ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    # Custom Palette
    NAVY = colors.HexColor('#0F172A')
    BLUE = colors.HexColor('#2563EB')
    DARK_GRAY = colors.HexColor('#334155')
    LIGHT_BG = colors.HexColor('#F8FAFC')
    RED = colors.HexColor('#DC2626')

    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=22, textColor=NAVY, spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle', parent=styles['Normal'], fontName='Helvetica', fontSize=11, textColor=DARK_GRAY, spaceAfter=15
    )
    heading2 = ParagraphStyle(
        'Head2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=14, textColor=BLUE, spaceBefore=12, spaceAfter=8
    )

    # Header
    story.append(Paragraph("Bharat Forge & Steel Manufacturing Pvt. Ltd.", title_style))
    story.append(Paragraph("Audit Analytics & Internal Control Monitoring — Executive Flagged Exceptions Report (FY 2025-26)", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=BLUE, spaceAfter=15))

    # Key Summary Metrics
    total_exceptions = AuditException.objects.count()
    critical_count = AuditException.objects.filter(severity='CRITICAL').count()
    high_count = AuditException.objects.filter(severity='HIGH').count()
    total_exposure = sum([float(e.amount) for e in AuditException.objects.all()])

    summary_data = [
        ['Total Audit Exceptions', 'Critical Severity', 'High Severity', 'Potential Exposure (INR)'],
        [str(total_exceptions), str(critical_count), str(high_count), f"₹{total_exposure:,.2f}"]
    ]
    t_summary = Table(summary_data, colWidths=[130, 120, 120, 170])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BACKGROUND', (0,1), (-1,1), LIGHT_BG),
        ('TEXTCOLOR', (0,1), (-1,1), NAVY),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 20))

    # Top Exceptions Table
    story.append(Paragraph("Top Risk Exceptions Requiring Auditor Action", heading2))
    
    top_exceptions = AuditException.objects.all().order_by('-risk_score')[:15]
    table_rows = [['ID', 'Exception Type', 'Tx Type', 'Risk', 'Severity', 'Vendor / Entity', 'Amount']]
    
    for exc in top_exceptions:
        v_name = exc.vendor.vendor_name if exc.vendor else 'Internal'
        table_rows.append([
            f"EXC-{exc.exception_id}",
            exc.exception_type[:30],
            exc.transaction_type,
            str(exc.risk_score),
            exc.severity,
            v_name[:22],
            f"₹{float(exc.amount):,.2f}"
        ])

    t_exc = Table(table_rows, colWidths=[55, 150, 65, 40, 60, 110, 60])
    t_exc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BLUE),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (3,0), (3,-1), 'CENTER'),
        ('ALIGN', (6,0), (6,-1), 'RIGHT'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG]),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    story.append(t_exc)

    doc.build(story)
    buffer.seek(0)
    return buffer
