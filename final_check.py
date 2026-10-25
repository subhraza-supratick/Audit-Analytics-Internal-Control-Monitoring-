import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'audit_project.settings')
django.setup()
from django.test import Client
from django.test.utils import setup_test_environment
setup_test_environment()
c = Client()
pages = [
    '/', '/dashboard/exceptions/', '/dashboard/financial/',
    '/dashboard/vendors/', '/transactions/', '/reports/pdf/',
    '/reports/csv/', '/api/dashboard/kpis/',
]
all_ok = True
for url in pages:
    r = c.get(url)
    ok = r.status_code == 200
    if not ok:
        all_ok = False
    status = 'PASS' if ok else 'FAIL'
    print(f'[{status}] {r.status_code} {url}')
print('ALL OK' if all_ok else 'FAILURES DETECTED')
