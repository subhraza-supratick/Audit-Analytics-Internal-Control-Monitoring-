from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, Count, Avg, F, Q
from transactions.models import (
    Invoice, Payment, PurchaseOrder, EmployeeExpense, Vendor, Employee, AuditException, Department, AuditLog
)

from django.contrib import messages
from analytics.etl import process_etl_upload

def landing_page_view(request):
    total_tx_val = float(Invoice.objects.aggregate(total=Sum('amount'))['total'] or 0.0)
    total_tx_count = Invoice.objects.count()
    exceptions = AuditException.objects.all()
    total_exceptions = exceptions.count()
    high_critical = exceptions.filter(severity__in=['HIGH', 'CRITICAL']).count()

    return render(request, 'dashboard/landing.html', {
        'total_tx_val': total_tx_val,
        'total_tx_count': total_tx_count,
        'total_exceptions': total_exceptions,
        'high_critical': high_critical,
        'is_empty': (total_tx_count == 0)
    })

def executive_overview(request):
    upload_report = None
    if request.method == 'POST':
        if request.FILES.get('file'):
            file_obj = request.FILES['file']
            upload_report = process_etl_upload(file_obj)
            if 'error' in upload_report:
                messages.error(request, upload_report['error'])
            else:
                messages.success(request, f"Successfully uploaded and ingested '{file_obj.name}'! Ingested {upload_report['records_persisted']} records with {upload_report['data_quality_score']}% Quality Score and detected {upload_report.get('audit_exceptions_flagged', 0)} exceptions.")
        else:
            messages.error(request, "Please attach a valid CSV or Excel (.xlsx) file before submitting.")

    total_tx_val = float(Invoice.objects.aggregate(total=Sum('amount'))['total'] or 0.0)
    total_tx_count = Invoice.objects.count()
    exceptions = AuditException.objects.all()
    total_exceptions = exceptions.count()
    high_critical = exceptions.filter(severity__in=['HIGH', 'CRITICAL']).count()
    total_exposure = float(exceptions.aggregate(total=Sum('amount'))['total'] or 0.0)
    exception_rate = round((total_exceptions / total_tx_count) * 100, 2) if total_tx_count > 0 else 0.0

    recent_exceptions = exceptions.select_related('vendor').order_by('-risk_score')[:6]
    
    # Severity & Status breakdown for charts
    severity_dist = list(exceptions.values('severity').annotate(count=Count('exception_id')))
    status_dist = list(exceptions.values('status').annotate(count=Count('exception_id')))

    return render(request, 'dashboard/index.html', {
        'total_tx_val': total_tx_val,
        'total_tx_count': total_tx_count,
        'total_exceptions': total_exceptions,
        'high_critical': high_critical,
        'total_exposure': total_exposure,
        'exception_rate': exception_rate,
        'recent_exceptions': recent_exceptions,
        'severity_dist': severity_dist,
        'status_dist': status_dist,
        'upload_report': upload_report,
        'is_empty': (total_tx_count == 0)
    })

def financial_analysis(request):
    vendor_spend = Vendor.objects.annotate(
        total_spend=Sum('invoices__amount'),
        invoice_count=Count('invoices')
    ).order_by('-total_spend')[:10]

    dept_spend = Department.objects.annotate(
        total_spend=Sum('purchaseorder__amount'),
        po_count=Count('purchaseorder')
    ).order_by('-total_spend')

    payment_summary = Payment.objects.aggregate(
        total=Sum('amount'),
        avg=Avg('amount'),
        cnt=Count('payment_id')
    )

    return render(request, 'dashboard/financial.html', {
        'vendor_spend': vendor_spend,
        'dept_spend': dept_spend,
        'payment_summary': payment_summary,
    })

def audit_exceptions_view(request):
    severity = request.GET.get('severity')
    status = request.GET.get('status')
    search_q = request.GET.get('q', '')

    exceptions = AuditException.objects.select_related('vendor').order_by('-risk_score')
    
    if severity:
        exceptions = exceptions.filter(severity=severity.upper())
    if status:
        exceptions = exceptions.filter(status=status.upper())
    if search_q:
        exceptions = exceptions.filter(
            Q(exception_type__icontains=search_q) |
            Q(transaction_id__icontains=search_q) |
            Q(description__icontains=search_q) |
            Q(vendor__vendor_name__icontains=search_q)
        )

    return render(request, 'dashboard/exceptions.html', {
        'exceptions': exceptions[:100],
        'current_severity': severity,
        'current_status': status,
        'search_q': search_q,
    })

def vendor_risk_matrix(request):
    vendors = Vendor.objects.annotate(
        total_spend=Sum('invoices__amount'),
        tx_count=Count('invoices'),
        exception_count=Count('auditexception')
    ).order_by('-total_spend')

    return render(request, 'dashboard/vendor_risk.html', {
        'vendors': vendors
    })

def investigation_detail(request, pk):
    exc = get_object_or_404(AuditException, pk=pk)
    logs = AuditLog.objects.filter(entity__contains=str(exc.exception_id)).order_by('-timestamp')
    
    related_invoice = Invoice.objects.filter(invoice_id=exc.transaction_id).first()
    related_payment = Payment.objects.filter(payment_id=exc.transaction_id).first()
    related_po = PurchaseOrder.objects.filter(po_id=exc.transaction_id).first()

    return render(request, 'dashboard/investigation.html', {
        'exception': exc,
        'logs': logs,
        'related_invoice': related_invoice,
        'related_payment': related_payment,
        'related_po': related_po,
    })

def interview_prep_view(request):
    return render(request, 'interview/index.html')

def custom_404_view(request, exception=None):
    return render(request, '404.html', status=404)

def audit_policy_view(request):
    return render(request, 'dashboard/audit_policy.html')
