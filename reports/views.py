import csv
from django.shortcuts import render
from django.http import HttpResponse
from reports.generator import generate_pdf_audit_report
from transactions.models import AuditException, Vendor, Invoice, Payment

def reports_index(request):
    exceptions = AuditException.objects.all().order_by('-risk_score')
    return render(request, 'reports/index.html', {
        'exceptions_count': exceptions.count(),
        'critical_count': exceptions.filter(severity='CRITICAL').count(),
        'high_count': exceptions.filter(severity='HIGH').count(),
    })

def export_pdf_report(request):
    pdf_buffer = generate_pdf_audit_report()
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Audit_Exceptions_Executive_Report.pdf"'
    return response

def export_csv_report(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="Audit_Exceptions_Export.csv"'

    writer = csv.writer(response)
    writer.writerow(['Exception ID', 'Transaction ID', 'Exception Type', 'Severity', 'Risk Score', 'ML Anomaly Score', 'Status', 'Vendor', 'Amount', 'Detected Date', 'Description'])

    for exc in AuditException.objects.all().order_by('-risk_score'):
        v_name = exc.vendor.vendor_name if exc.vendor else 'N/A'
        writer.writerow([
            f"EXC-{exc.exception_id}",
            exc.transaction_id,
            exc.exception_type,
            exc.severity,
            exc.risk_score,
            exc.ml_anomaly_score,
            exc.status,
            v_name,
            float(exc.amount),
            exc.detected_date.strftime('%Y-%m-%d %H:%M:%S'),
            exc.description
        ])
    return response
