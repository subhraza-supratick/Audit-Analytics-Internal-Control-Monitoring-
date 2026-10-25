import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'audit_project.settings')
django.setup()

from django.test import Client
from django.test.utils import setup_test_environment
setup_test_environment()

c = Client()

print('=' * 70)
print('POST ENDPOINTS & FUNCTIONAL LOGIC TESTS')
print('=' * 70)
all_passed = True

def check(ok, label):
    global all_passed
    icon = 'PASS' if ok else 'FAIL'
    if not ok:
        all_passed = False
    print(f'[{icon}] {label}')
    return ok

from transactions.models import AuditException, AuditLog
# Get a real existing exception PK
first_exc = AuditException.objects.order_by('exception_id').first()
if not first_exc:
    print('[WARN] No exceptions in DB — run audit engine first')
    exit(1)
exc_pk = first_exc.exception_id
print(f'  Testing with exception PK={exc_pk}')

# Test 1: Run audit engine via POST
resp = c.post('/audit/run/', {}, follow=True)
check(resp.status_code == 200, f'{resp.status_code}  POST /audit/run/ - Run Audit Engine')

# Refresh first_exc PK after audit re-ran
first_exc = AuditException.objects.order_by('exception_id').first()
exc_pk = first_exc.exception_id
print(f'  Refreshed exception PK={exc_pk} after audit run')

# Test 2: Exception status update via POST
resp = c.post(f'/audit/exceptions/{exc_pk}/status/', {
    'status': 'UNDER_REVIEW',
    'assigned_to': 'Senior Auditor QA',
    'review_notes': 'Test note'
}, follow=True)
check(resp.status_code == 200, f'{resp.status_code}  POST /audit/exceptions/{exc_pk}/status/ - Update Exception Status')

# Test 3: Verify exception status was actually updated in DB
exc = AuditException.objects.get(pk=exc_pk)
check(exc.status == 'UNDER_REVIEW' and exc.assigned_to == 'Senior Auditor QA',
      f'DB UPDATE VERIFIED: status={exc.status}, assigned_to={exc.assigned_to}')

# Test 3b: Verify audit log was created
log_exists = AuditLog.objects.filter(entity__contains=str(exc_pk)).exists()
check(log_exists, f'Audit Log trail created for exception {exc_pk}')

# Test 4: PDF export
resp = c.get('/reports/pdf/')
ct = resp.get('Content-Type', '')
check(resp.status_code == 200 and 'pdf' in ct,
      f'{resp.status_code} Content-Type={ct[:30]}  GET /reports/pdf/ - PDF Report')

# Test 5: CSV export
resp = c.get('/reports/csv/')
ct = resp.get('Content-Type', '')
check(resp.status_code == 200 and 'csv' in ct,
      f'{resp.status_code} Content-Type={ct[:30]}  GET /reports/csv/ - CSV Report')

# Test 6: API audit run via POST
resp = c.post('/api/audit/run/', content_type='application/json', data='{}')
check(resp.status_code in [200, 201], f'{resp.status_code}  POST /api/audit/run/ - API Audit Run')

# Refresh PK again
first_exc = AuditException.objects.order_by('exception_id').first()
exc_pk = first_exc.exception_id

# Test 7: SQL Explorer with live SQL via POST
resp = c.post('/analytics/sql/?query_id=q1', {
    'custom_sql': 'SELECT COUNT(*) as total FROM transactions_invoice'
})
check(resp.status_code == 200, f'{resp.status_code}  POST /analytics/sql/ - Live SQL Runner')

# Test 8: Transactions type switcher
for tx_type in ['invoices', 'payments', 'purchase_orders', 'expenses']:
    resp = c.get(f'/transactions/?type={tx_type}')
    check(resp.status_code == 200, f'{resp.status_code}  GET /transactions/?type={tx_type}')

# Test 9: Audit exceptions filter by severity
for sev in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
    resp = c.get(f'/dashboard/exceptions/?severity={sev}')
    check(resp.status_code == 200, f'{resp.status_code}  GET /dashboard/exceptions/?severity={sev}')

# Test 10: API PATCH exception status
import json
resp = c.patch(f'/api/exceptions/{exc_pk}/status/',
               json.dumps({'status': 'RESOLVED', 'review_notes': 'PATCH test resolved'}),
               content_type='application/json')
check(resp.status_code == 200, f'{resp.status_code}  PATCH /api/exceptions/{exc_pk}/status/')

# Test 11: Vendor Risk API
resp = c.get('/api/vendors/VEND-501/risk/')
check(resp.status_code == 200, f'{resp.status_code}  GET /api/vendors/VEND-501/risk/')

# Test 12: Exception search
resp = c.get('/dashboard/exceptions/?q=Duplicate')
check(resp.status_code == 200, f'{resp.status_code}  GET /dashboard/exceptions/?q=Duplicate - Search filter')

# Test 13: Role switch POST
resp = c.post('/accounts/switch-role/', {'role': 'ADMIN'}, follow=True)
check(resp.status_code == 200, f'{resp.status_code}  POST /accounts/switch-role/ - Role Switch')

# Test 14: Pagination - page 2 of transactions
resp = c.get('/transactions/?type=invoices&page=2')
check(resp.status_code == 200, f'{resp.status_code}  GET /transactions/?type=invoices&page=2 - Pagination')

# Test 15: API exception severity filter
resp = c.get('/api/exceptions/?severity=CRITICAL')
check(resp.status_code == 200, f'{resp.status_code}  GET /api/exceptions/?severity=CRITICAL - API Severity Filter')

# Test 16: Investigation detail page with real PK
resp = c.get(f'/dashboard/exceptions/{exc_pk}/')
check(resp.status_code == 200, f'{resp.status_code}  GET /dashboard/exceptions/{exc_pk}/ - Investigation Detail')

# Test 17: API exception detail endpoint
resp = c.get(f'/api/exceptions/{exc_pk}/')
check(resp.status_code == 200, f'{resp.status_code}  GET /api/exceptions/{exc_pk}/ - API Exception Detail')

# Test 18: Status filter by status 
for status_code in ['OPEN', 'UNDER_REVIEW']:
    resp = c.get(f'/dashboard/exceptions/?status={status_code}')
    check(resp.status_code == 200, f'{resp.status_code}  GET /dashboard/exceptions/?status={status_code}')

# Test 19: SQL queries - all 10 predefined queries
for q_id in ['q1','q2','q3','q4','q5','q6','q7','q8','q9','q10']:
    resp = c.get(f'/analytics/sql/?query_id={q_id}')
    check(resp.status_code == 200, f'{resp.status_code}  GET /analytics/sql/?query_id={q_id}')

# Test 20: API KPIs returns correct structure
resp = c.get('/api/dashboard/kpis/')
import json as j
data = j.loads(resp.content)
required_keys = ['total_transactions_count', 'total_transactions_value', 'total_exceptions', 'high_critical_exceptions']
all_keys_present = all(k in data for k in required_keys)
check(all_keys_present, f'API KPIs structure valid: {list(data.keys())}')

# Test 21: Upload real CSV file via ETL web endpoint
with open('sample_audit_dataset.csv', 'rb') as fp:
    resp = c.post('/analytics/etl/', {'file': fp}, follow=True)
check(resp.status_code == 200, f'{resp.status_code}  POST /analytics/etl/ - Ingest CSV Dataset')

# Test 22: Upload real XLSX file via ETL web endpoint
with open('sample_audit_dataset.xlsx', 'rb') as fp:
    resp = c.post('/analytics/etl/', {'file': fp}, follow=True)
check(resp.status_code == 200, f'{resp.status_code}  POST /analytics/etl/ - Ingest XLSX Excel Dataset')

# Test 23: Upload CSV file via REST API
with open('sample_audit_dataset.csv', 'rb') as fp:
    resp = c.post('/api/upload/', {'file': fp})
check(resp.status_code == 200, f'{resp.status_code}  POST /api/upload/ - Ingest via REST API')

print('=' * 70)
print('ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED - see above')
