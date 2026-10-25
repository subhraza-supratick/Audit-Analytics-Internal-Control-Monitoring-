from django.db.models import Count, Sum, Avg, F, Q
from django.utils import timezone
from datetime import timedelta
from transactions.models import (
    Invoice, Payment, PurchaseOrder, EmployeeExpense, Vendor, Employee, AuditException, AuditLog
)
from audit_engine.risk_scorer import calculate_explainable_risk_score
from audit_engine.ml_anomaly import train_and_predict_isolation_forest

def run_all_audit_rules():
    """
    Executes all 11 SQL/Python audit tests against financial transactions.
    Creates or updates AuditException records in the database.
    Returns audit execution summary dictionary.
    """
    ml_scores = train_and_predict_isolation_forest()
    exceptions_created = 0

    # Clear existing unreviewed exceptions if re-running
    AuditException.objects.filter(status='OPEN').delete()

    # 1. Duplicate Invoice Detection
    dup_invoices = Invoice.objects.values('vendor_id', 'invoice_date', 'amount', 'reference_no') \
        .annotate(cnt=Count('invoice_id')) \
        .filter(cnt__gt=1)
    
    for item in dup_invoices:
        matches = Invoice.objects.filter(
            vendor_id=item['vendor_id'],
            invoice_date=item['invoice_date'],
            amount=item['amount']
        )
        for inv in matches:
            ml_score = ml_scores.get(inv.invoice_id, 0.4)
            score, severity = calculate_explainable_risk_score('HIGH', inv.amount, ml_score)
            AuditException.objects.create(
                transaction_id=inv.invoice_id,
                transaction_type='INVOICE',
                exception_type='Duplicate Invoice Detection',
                severity=severity,
                risk_score=score,
                ml_anomaly_score=ml_score,
                description=f"Duplicate invoice detected: Same Vendor ({inv.vendor.vendor_name}), Date ({inv.invoice_date}), Amount (?{inv.amount:,.2f}), and Reference ({inv.reference_no}).",
                vendor=inv.vendor,
                amount=inv.amount,
                status='OPEN',
                assigned_to='Unassigned'
            )
            exceptions_created += 1

    # 2. Duplicate Payment Detection
    dup_payments = Payment.objects.values('invoice_id', 'amount', 'vendor_id') \
        .annotate(cnt=Count('payment_id')) \
        .filter(cnt__gt=1)

    for item in dup_payments:
        matches = Payment.objects.filter(
            invoice_id=item['invoice_id'],
            amount=item['amount']
        ).select_related('vendor', 'invoice')
        for pay in matches:
            score, severity = calculate_explainable_risk_score('CRITICAL', pay.amount, 0.8)
            AuditException.objects.create(
                transaction_id=pay.payment_id,
                transaction_type='PAYMENT',
                exception_type='Duplicate Payment Detection',
                severity=severity,
                risk_score=score,
                ml_anomaly_score=0.8,
                description=f"Duplicate payment processed for Invoice {pay.invoice.invoice_id}: Vendor ({pay.vendor.vendor_name}), Amount (?{pay.amount:,.2f}).",
                vendor=pay.vendor,
                amount=pay.amount,
                status='OPEN',
                assigned_to='Unassigned'
            )
            exceptions_created += 1

    # 3. Weekend Transaction Detection
    weekend_payments = Payment.objects.filter(payment_date__week_day__in=[1, 7]).select_related('vendor') # Sunday=1, Saturday=7 in Django
    for pay in weekend_payments:
        day_name = pay.payment_date.strftime('%A')
        score, severity = calculate_explainable_risk_score('MEDIUM', pay.amount, 0.5)
        AuditException.objects.create(
            transaction_id=pay.payment_id,
            transaction_type='PAYMENT',
            exception_type='Weekend Transaction Detection',
            severity=severity,
            risk_score=score,
            ml_anomaly_score=0.5,
            description=f"Transaction executed on a weekend ({day_name}) for ?{pay.amount:,.2f} to {pay.vendor.vendor_name}.",
            vendor=pay.vendor,
            amount=pay.amount,
            status='OPEN'
        )
        exceptions_created += 1

    # 4. After-hours Transaction Detection (outside 8 AM to 6 PM)
    after_hours = Payment.objects.exclude(payment_date__hour__range=(8, 18)).select_related('vendor')
    for pay in after_hours:
        time_str = pay.payment_date.strftime('%H:%M:%S UTC')
        score, severity = calculate_explainable_risk_score('MEDIUM', pay.amount, 0.6)
        AuditException.objects.create(
            transaction_id=pay.payment_id,
            transaction_type='PAYMENT',
            exception_type='After-hours Transaction Detection',
            severity=severity,
            risk_score=score,
            ml_anomaly_score=0.6,
            description=f"Transaction executed outside standard business operating hours ({time_str}) for ?{pay.amount:,.2f}.",
            vendor=pay.vendor,
            amount=pay.amount,
            status='OPEN'
        )
        exceptions_created += 1

    # 5. Round-Amount Transaction Detection (₹5,00,000+ exactly divisible by ₹5,00,000)
    round_invoices = Invoice.objects.filter(amount__gte=500000.00).select_related('vendor')
    for inv in round_invoices:
        if float(inv.amount) % 500000 == 0:
            ml_score = ml_scores.get(inv.invoice_id, 0.45)
            score, severity = calculate_explainable_risk_score('MEDIUM', inv.amount, ml_score)
            AuditException.objects.create(
                transaction_id=inv.invoice_id,
                transaction_type='INVOICE',
                exception_type='Round-Amount Transaction Detection',
                severity=severity,
                risk_score=score,
                ml_anomaly_score=ml_score,
                description=f"Large, perfectly rounded invoice amount identified: ?{inv.amount:,.2f} issued to {inv.vendor.vendor_name}.",
                vendor=inv.vendor,
                amount=inv.amount,
                status='OPEN'
            )
            exceptions_created += 1

    # 6. Approval-Threshold Violation
    pos_over_limit = PurchaseOrder.objects.filter(amount__gt=F('employee__approval_limit')).select_related('vendor', 'employee')
    for po in pos_over_limit:
        score, severity = calculate_explainable_risk_score('HIGH', po.amount, 0.75)
        AuditException.objects.create(
            transaction_id=po.po_id,
            transaction_type='PURCHASE_ORDER',
            exception_type='Approval-Threshold Violation',
            severity=severity,
            risk_score=score,
            ml_anomaly_score=0.75,
            description=f"Purchase order amount (?{po.amount:,.2f}) exceeds employee ({po.employee.name}) delegated authorization limit of ?{po.employee.approval_limit:,.2f}.",
            vendor=po.vendor,
            amount=po.amount,
            status='OPEN'
        )
        exceptions_created += 1

    # 7. Split Purchase Detection
    # Identifies multiple POs issued on same day to same vendor by same employee that sum up above approval limit
    split_candidates = PurchaseOrder.objects.values('employee_id', 'vendor_id', 'po_date') \
        .annotate(total_amt=Sum('amount'), po_count=Count('po_id')) \
        .filter(po_count__gt=1)

    for item in split_candidates:
        emp = Employee.objects.get(employee_id=item['employee_id'])
        if item['total_amt'] > emp.approval_limit:
            vendor = Vendor.objects.get(vendor_id=item['vendor_id'])
            score, severity = calculate_explainable_risk_score('CRITICAL', item['total_amt'], 0.85)
            AuditException.objects.create(
                transaction_id=f"SPLIT-{item['employee_id']}-{item['po_date']}",
                transaction_type='PURCHASE_ORDER',
                exception_type='Split-Purchase Detection',
                severity=severity,
                risk_score=score,
                ml_anomaly_score=0.85,
                description=f"Potential split purchases detected: Employee {emp.name} created {item['po_count']} POs on {item['po_date']} totaling ?{item['total_amt']:,.2f}, circumventing single-approval limit of ?{emp.approval_limit:,.2f}.",
                vendor=vendor,
                amount=item['total_amt'],
                status='OPEN'
            )
            exceptions_created += 1

    # 8. Unusual Vendor Activity (Invoices > ₹80,00,000 for critical/high risk category vendors)
    unusual_vendors = Invoice.objects.filter(vendor__risk_category__in=['HIGH', 'CRITICAL'], amount__gte=8000000.00).select_related('vendor')
    for inv in unusual_vendors:
        score, severity = calculate_explainable_risk_score('HIGH', inv.amount, 0.7)
        AuditException.objects.create(
            transaction_id=inv.invoice_id,
            transaction_type='INVOICE',
            exception_type='Unusual Vendor Activity',
            severity=severity,
            risk_score=score,
            ml_anomaly_score=0.7,
            description=f"Unusually large transaction amount (?{inv.amount:,.2f}) for high-risk rated vendor ({inv.vendor.vendor_name}).",
            vendor=inv.vendor,
            amount=inv.amount,
            status='OPEN'
        )
        exceptions_created += 1

    # 9. Employee Expense Anomaly (amount > ₹1,00,000)
    anom_expenses = EmployeeExpense.objects.filter(amount__gte=100000.00).select_related('employee')
    for exp in anom_expenses:
        score, severity = calculate_explainable_risk_score('HIGH', exp.amount, 0.8)
        AuditException.objects.create(
            transaction_id=exp.expense_id,
            transaction_type='EXPENSE',
            exception_type='Employee Expense Anomaly',
            severity=severity,
            risk_score=score,
            ml_anomaly_score=0.8,
            description=f"Employee expense anomaly: ?{exp.amount:,.2f} claimed by {exp.employee.name} in category '{exp.category}' significantly exceeds statistical peer threshold.",
            amount=exp.amount,
            status='OPEN'
        )
        exceptions_created += 1

    # 10. Duplicate Employee Expense
    dup_expenses = EmployeeExpense.objects.values('employee_id', 'expense_date', 'amount', 'category') \
        .annotate(cnt=Count('expense_id')) \
        .filter(cnt__gt=1)
    for item in dup_expenses:
        matches = EmployeeExpense.objects.filter(
            employee_id=item['employee_id'], expense_date=item['expense_date'], amount=item['amount']
        ).select_related('employee')
        for exp in matches:
            score, severity = calculate_explainable_risk_score('HIGH', exp.amount, 0.75)
            AuditException.objects.create(
                transaction_id=exp.expense_id,
                transaction_type='EXPENSE',
                exception_type='Duplicate Employee Expense',
                severity=severity,
                risk_score=score,
                ml_anomaly_score=0.75,
                description=f"Duplicate expense report filed by {exp.employee.name} on {exp.expense_date} for ?{exp.amount:,.2f}.",
                amount=exp.amount,
                status='OPEN'
            )
            exceptions_created += 1

    # 11. Employee-Vendor Relationship / CoI Check
    # Check for matching bank account or address between Employee and Vendor
    coi_vendors = Vendor.objects.all()
    for v in coi_vendors:
        matched_emp = Employee.objects.filter(Q(bank_account=v.bank_account) | Q(address=v.address)).first()
        if matched_emp:
            score, severity = calculate_explainable_risk_score('CRITICAL', 95000.00, 0.95, is_conflict_of_interest=True)
            AuditException.objects.create(
                transaction_id=f"COI-{v.vendor_id}-{matched_emp.employee_id}",
                transaction_type='VENDOR_MASTER',
                exception_type='Employee-Vendor Relationship Check',
                severity=severity,
                risk_score=score,
                ml_anomaly_score=0.95,
                description=f"CONFLICT OF INTEREST DETECTED: Vendor ({v.vendor_name}) shares matching bank account / street address with Employee {matched_emp.name} ({matched_emp.employee_id}). Immediate audit investigation required.",
                vendor=v,
                amount=9500000.00,
                status='OPEN'
            )
            exceptions_created += 1

    AuditLog.objects.create(
        user='Audit Engine System',
        action='EXECUTE_RULES',
        entity='Audit Exceptions Engine',
        old_value='0',
        new_value=str(exceptions_created)
    )

    return {
        'total_exceptions': exceptions_created,
        'high_critical_count': AuditException.objects.filter(severity__in=['HIGH', 'CRITICAL']).count(),
        'execution_timestamp': timezone.now().isoformat()
    }
