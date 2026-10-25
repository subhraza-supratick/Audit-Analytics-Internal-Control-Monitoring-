from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Count, Avg
from django.shortcuts import get_object_or_404
from transactions.models import Invoice, AuditException, Vendor, Payment, AuditLog
from transactions.serializers import InvoiceSerializer, AuditExceptionSerializer, VendorSerializer
from audit_engine.rules import run_all_audit_rules
from analytics.etl import process_etl_upload

@api_view(['POST'])
@permission_classes([AllowAny])
def upload_file_api(request):
    if 'file' not in request.FILES:
        return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)
    file_obj = request.FILES['file']
    result = process_etl_upload(file_obj)
    if 'error' in result:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)
    return Response(result, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def list_transactions_api(request):
    invoices = Invoice.objects.select_related('vendor').order_by('-invoice_date')[:50]
    serializer = InvoiceSerializer(invoices, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def list_exceptions_api(request):
    severity = request.GET.get('severity')
    exceptions = AuditException.objects.select_related('vendor').order_by('-risk_score')
    if severity:
        exceptions = exceptions.filter(severity=severity.upper())
    serializer = AuditExceptionSerializer(exceptions[:100], many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def exception_detail_api(request, pk):
    exc = get_object_or_404(AuditException, pk=pk)
    serializer = AuditExceptionSerializer(exc)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def vendor_risk_api(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    exceptions = AuditException.objects.filter(vendor=vendor)
    invoices = Invoice.objects.filter(vendor=vendor)
    total_spend = invoices.aggregate(total=Sum('amount'))['total'] or 0.0
    
    return Response({
        'vendor_id': vendor.vendor_id,
        'vendor_name': vendor.vendor_name,
        'risk_category': vendor.risk_category,
        'total_spend': float(total_spend),
        'transaction_count': invoices.count(),
        'exception_count': exceptions.count(),
        'exceptions': AuditExceptionSerializer(exceptions, many=True).data
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_kpis_api(request):
    total_tx_val = Invoice.objects.aggregate(total=Sum('amount'))['total'] or 0.0
    total_exceptions = AuditException.objects.count()
    high_critical = AuditException.objects.filter(severity__in=['HIGH', 'CRITICAL']).count()
    potential_exposure = sum([float(e.amount) for e in AuditException.objects.all()])
    total_tx_count = max(1, Invoice.objects.count())
    exception_rate = round((total_exceptions / total_tx_count) * 100, 2)

    return Response({
        'total_transactions_count': total_tx_count,
        'total_transactions_value': float(total_tx_val),
        'total_exceptions': total_exceptions,
        'high_critical_exceptions': high_critical,
        'potential_financial_exposure': potential_exposure,
        'exception_rate_percentage': exception_rate
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_trends_api(request):
    severity_dist = list(AuditException.objects.values('severity').annotate(count=Count('exception_id')))
    status_dist = list(AuditException.objects.values('status').annotate(count=Count('exception_id')))
    top_vendors = list(Invoice.objects.values('vendor__vendor_name').annotate(total=Sum('amount')).order_by('-total')[:5])

    return Response({
        'severity_distribution': severity_dist,
        'status_distribution': status_dist,
        'top_vendors_spend': top_vendors
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def run_audit_api(request):
    summary = run_all_audit_rules()
    return Response(summary, status=status.HTTP_200_OK)

@api_view(['PATCH', 'POST'])
@permission_classes([AllowAny])
def update_exception_status_api(request, pk):
    exc = get_object_or_404(AuditException, pk=pk)
    new_status = request.data.get('status')
    if new_status in ['OPEN', 'UNDER_REVIEW', 'RESOLVED', 'FALSE_POSITIVE']:
        exc.status = new_status
        exc.assigned_to = request.data.get('assigned_to', exc.assigned_to)
        exc.review_notes = request.data.get('review_notes', exc.review_notes)
        exc.save()
        return Response(AuditExceptionSerializer(exc).data)
    return Response({'error': 'Invalid status value'}, status=status.HTTP_400_BAD_REQUEST)
