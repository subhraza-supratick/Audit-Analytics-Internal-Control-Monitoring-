from audit_engine.rules import run_all_audit_rules
from transactions.models import AuditException
from django.db.models import Sum, Count

print('Running full audit engine on Indian real-world scenario...')
result = run_all_audit_rules()

print()
print('=== AUDIT RESULTS (INR Scale) ===')
print(f'Total Exceptions Flagged : {result["total_exceptions"]}')
print(f'High/Critical Count      : {result["high_critical_count"]}')
print(f'Execution Timestamp      : {result["execution_timestamp"]}')
print()
print('Breakdown by Exception Type:')
for r in AuditException.objects.values('exception_type').annotate(
    cnt=Count('exception_id'), total=Sum('amount')
).order_by('-cnt'):
    print(f'  {r["cnt"]:3d}  {r["exception_type"][:50]:50s}  INR {float(r["total"]):>16,.2f}')

print()
print('Top 10 Highest Risk Exceptions:')
for exc in AuditException.objects.order_by('-risk_score')[:10]:
    v = exc.vendor.vendor_name if exc.vendor else 'Internal'
    print(f'  [{exc.severity:8s}] Score={exc.risk_score:3d}  INR {float(exc.amount):>14,.2f}  {exc.exception_type[:40]}  [{v[:30]}]')
