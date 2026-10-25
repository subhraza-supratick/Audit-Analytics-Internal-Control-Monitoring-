from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from transactions.models import (
    Invoice, PurchaseOrder, Payment, EmployeeExpense, 
    Vendor, Employee, Department, AuditException, AuditLog
)
from transactions.seed_data import generate_synthetic_data

def transaction_list(request):
    tx_type = request.GET.get('type', 'invoices')
    query = request.GET.get('q', '')
    
    if tx_type == 'invoices':
        items = Invoice.objects.select_related('vendor', 'po').order_by('-invoice_date')
        if query:
            items = items.filter(invoice_id__icontains=query) | items.filter(vendor__vendor_name__icontains=query)
    elif tx_type == 'payments':
        items = Payment.objects.select_related('vendor', 'invoice').order_by('-payment_date')
        if query:
            items = items.filter(payment_id__icontains=query) | items.filter(vendor__vendor_name__icontains=query)
    elif tx_type == 'purchase_orders':
        items = PurchaseOrder.objects.select_related('vendor', 'employee', 'department').order_by('-po_date')
        if query:
            items = items.filter(po_id__icontains=query) | items.filter(vendor__vendor_name__icontains=query)
    else:
        items = EmployeeExpense.objects.select_related('employee', 'department').order_by('-expense_date')
        if query:
            items = items.filter(expense_id__icontains=query) | items.filter(employee__name__icontains=query)

    paginator = Paginator(items, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'transactions/list.html', {
        'page_obj': page_obj,
        'tx_type': tx_type,
        'query': query
    })

def seed_data_view(request):
    if request.method == 'POST':
        try:
            count = int(request.POST.get('count', 1000))
            if count <= 0 or count > 10000:
                count = 1000
            generate_synthetic_data(num_records=count, clear_existing=True)
            from audit_engine.rules import run_audit_rules
            run_audit_rules()
            messages.success(request, f"Successfully generated {count} synthetic financial records and executed all 11 audit heuristics!")
        except Exception as e:
            messages.error(request, f"Failed to seed demo data: {str(e)}")
        return redirect('dashboard_overview')
    return redirect('dashboard_overview')

def clear_data_view(request):
    if request.method == 'POST':
        AuditException.objects.all().delete()
        AuditLog.objects.all().delete()
        Payment.objects.all().delete()
        Invoice.objects.all().delete()
        PurchaseOrder.objects.all().delete()
        EmployeeExpense.objects.all().delete()
        Vendor.objects.all().delete()
        Employee.objects.all().delete()
        Department.objects.all().delete()
        messages.info(request, "Database cleared to fresh slate. System is now ready for your custom CSV/Excel dataset upload!")
        return redirect('dashboard_overview')
    return redirect('dashboard_overview')
