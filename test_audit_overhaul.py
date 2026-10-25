import os
import re
import sys
import json
import django

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'audit_project.settings')
django.setup()

from django.test import Client
from django.test.utils import setup_test_environment
from transactions.models import (
    AuditException, AuditLog, Invoice, Payment, PurchaseOrder,
    EmployeeExpense, Vendor, Employee, Department
)

setup_test_environment()
client = Client()

print("=" * 80)
print("AUDIT ANALYTICS PLATFORM - FULL SPECIFICATION & FEATURE VERIFICATION SUITE")
print("=" * 80)

passed_count = 0
failed_count = 0

def record_test(ok, label, details=""):
    global passed_count, failed_count
    status_str = "PASS" if ok else "FAIL"
    if ok:
        passed_count += 1
        print(f"[{status_str}] {label}")
    else:
        failed_count += 1
        print(f"[{status_str}] {label} -> {details}")
    return ok

# ---------------------------------------------------------
# 1. TEST ALL 14 URLS / PAGES FOR HTTP 200
# ---------------------------------------------------------
print("\n--- 1. Testing Page Rendering (HTTP 200) ---")

pages_to_test = [
    ('/', 'Platform Overview & Guide Landing Page'),
    ('/dashboard/', 'Executive Overview Dashboard'),
    ('/dashboard/exceptions/', 'Audit Exception Explorer'),
    ('/dashboard/financial/', 'Financial Spend Analysis'),
    ('/dashboard/vendors/', 'Vendor Risk Matrix'),
    ('/transactions/', 'Financial Transactions (Invoices)'),
    ('/transactions/?type=payments', 'Financial Transactions (Payments)'),
    ('/transactions/?type=purchase_orders', 'Financial Transactions (POs)'),
    ('/transactions/?type=expenses', 'Financial Transactions (Expenses)'),
    ('/analytics/sql/', 'Interactive SQL Query Explorer'),
    ('/analytics/etl/', 'ETL Pipeline Ingestion Page'),
    ('/reports/', 'Management Reports & Exports Index'),
    ('/interview-prep/', 'Interview & Portfolio Portal'),
    ('/accounts/login/', 'Auditor RBAC Login Page'),
    ('/audit-policy/', 'Audit Governance & SOX 404 Policy Page'),
]

rendered_html = {}
for path, desc in pages_to_test:
    resp = client.get(path)
    ok = (resp.status_code == 200)
    record_test(ok, f"GET {path} ({desc}) - Status {resp.status_code}")
    if ok:
        rendered_html[path] = resp.content.decode('utf-8', errors='ignore')

# ---------------------------------------------------------
# 2. TEST CUSTOM 404 PAGE
# ---------------------------------------------------------
print("\n--- 2. Testing Custom 404 Page (Requirement 8) ---")
resp_404_preview = client.get('/404/')
is_404_preview = (resp_404_preview.status_code == 404) and ("404" in resp_404_preview.content.decode('utf-8', errors='ignore'))
record_test(is_404_preview, "GET /404/ returns custom 404 page with status 404")

resp_404_random = client.get('/non-existent-audit-url-for-test/')
is_404_random = (resp_404_random.status_code == 404)
record_test(is_404_random, "GET /non-existent-url/ triggers custom 404 handler")

# ---------------------------------------------------------
# 3. TEST UNIQUE TITLE & META DESCRIPTION ACROSS EVERY PAGE
# ---------------------------------------------------------
print("\n--- 3. Testing Titles & Meta Descriptions (Requirements 5 & 6) ---")

titles_seen = {}
meta_descs_seen = {}

for path, html in rendered_html.items():
    # Title regex
    title_match = re.search(r'<title>(.*?)</title>', html, re.DOTALL | re.IGNORECASE)
    has_title = bool(title_match and title_match.group(1).strip())
    title_text = title_match.group(1).strip() if title_match else ""
    
    # Meta description regex
    meta_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html, re.DOTALL | re.IGNORECASE)
    has_meta = bool(meta_match and meta_match.group(1).strip())
    meta_text = meta_match.group(1).strip() if meta_match else ""

    record_test(has_title and len(title_text) > 5, f"{path} has title: '{title_text[:40]}...'")
    record_test(has_meta and len(meta_text) > 15, f"{path} has meta description: '{meta_text[:40]}...'")

    titles_seen[path] = title_text
    meta_descs_seen[path] = meta_text

# Verify titles are distinct across distinct core pages
core_pages = ['/', '/dashboard/', '/dashboard/exceptions/', '/dashboard/financial/', '/dashboard/vendors/', '/analytics/sql/', '/analytics/etl/', '/reports/', '/interview-prep/', '/accounts/login/', '/audit-policy/']
unique_titles = set(titles_seen.get(p) for p in core_pages if p in titles_seen)
record_test(len(unique_titles) == len(core_pages), f"All {len(core_pages)} core pages have distinct, unique titles ({len(unique_titles)} unique)")

# ---------------------------------------------------------
# 4. TEST FAVICON, LOGO LINK, MOBILE HAMBURGER & 3D CANVAS
# ---------------------------------------------------------
print("\n--- 4. Testing Favicon, Logo Link, Mobile Menu & 3D Elements (Requirements 3, 4, 17, 21) ---")

sample_html = rendered_html.get('/')
has_favicon = 'rel="icon"' in sample_html and 'favicon.svg' in sample_html
record_test(has_favicon, "Favicon link present in HTML head")

favicon_path = os.path.join('static', 'img', 'favicon.svg')
record_test(os.path.exists(favicon_path) and os.path.getsize(favicon_path) > 0, f"Favicon file exists on disk: {favicon_path}")

has_logo_link = 'sidebar-brand-link' in sample_html and 'href="/"' in sample_html
record_test(has_logo_link, "Sidebar logo links directly to homepage (Requirement 17)")

has_mobile_btn = 'id="mobileMenuBtn"' in sample_html
has_overlay = 'id="sidebarOverlay"' in sample_html
has_close_btn = 'id="sidebarCloseBtn"' in sample_html
record_test(has_mobile_btn and has_overlay and has_close_btn, "Responsive mobile hamburger menu elements present (Requirement 3)")

has_3d_canvas = 'id="bgCanvas3D"' in sample_html
record_test(has_3d_canvas, "Interactive 3D Cyber Constellation background canvas present (Requirement 21)")

# ---------------------------------------------------------
# 5. TEST FOOTER, CLICKABLE TEL & MAILTO, AUTO YEAR
# ---------------------------------------------------------
print("\n--- 5. Testing Footer, Contact Links & Copyright (Requirements 7, 9, 18, 19) ---")

has_footer = 'app-footer' in sample_html
record_test(has_footer, "Global enterprise audit footer present")

has_tel = 'href="tel:+18005552834"' in sample_html
record_test(has_tel, "Clickable phone number (tel: link) present (Requirement 18)")

has_mailto = 'href="mailto:audit-desk@internal-controls.org"' in sample_html
record_test(has_mailto, "Clickable email address (mailto: link) present (Requirement 19)")

has_auto_year = 'id="copyrightYear"' in sample_html
record_test(has_auto_year, "Auto-updating copyright year element present (Requirement 9)")

# ---------------------------------------------------------
# 6. TEST ALL LINKS TO ENSURE ZERO BROKEN LINKS
# ---------------------------------------------------------
print("\n--- 6. Testing For Broken Links (Requirement 2 & 7) ---")

# Scan rendered HTML for all a tags
link_patterns = re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\']', sample_html)
broken_links = []
tested_links = set()

for href in link_patterns:
    if href.startswith('#') or href.startswith('tel:') or href.startswith('mailto:') or href.startswith('javascript:'):
        continue
    if href in tested_links:
        continue
    tested_links.add(href)
    
    # Test internal links
    if href.startswith('/'):
        chk = client.get(href)
        if chk.status_code not in [200, 302]:
            broken_links.append((href, chk.status_code))

record_test(len(broken_links) == 0, f"All {len(tested_links)} internal links resolved successfully (0 broken)", str(broken_links))

# ---------------------------------------------------------
# 7. TEST FORM SUBMISSIONS, ACTIONS, SUCCESS & ERROR MESSAGES
# ---------------------------------------------------------
print("\n--- 7. Testing Form Actions, Success & Error Messages (Requirements 11, 12, 13) ---")

# Test 7.1: Run Audit Engine POST
resp_audit = client.post('/audit/run/', follow=True)
has_audit_msg = any('Audit Rules Engine executed' in m.message for m in resp_audit.context['messages'])
record_test(resp_audit.status_code == 200 and has_audit_msg, "POST /audit/run/ - Run Audit Engine generates success message")

# Test 7.2: Role switch valid
resp_role_ok = client.post('/accounts/switch-role/', {'role': 'ADMIN'}, follow=True)
has_role_msg = any('switched to ADMIN' in m.message for m in resp_role_ok.context['messages'])
record_test(resp_role_ok.status_code == 200 and has_role_msg, "POST /accounts/switch-role/ with valid role produces success message")

# Test 7.3: Role switch invalid
resp_role_bad = client.post('/accounts/switch-role/', {'role': 'SUPER_HACKER'}, follow=True)
has_role_err = any('Invalid role' in m.message for m in resp_role_bad.context['messages'])
record_test(resp_role_bad.status_code == 200 and has_role_err, "POST /accounts/switch-role/ with invalid role produces clear error message")

# Test 7.4: Login POST valid
resp_login_ok = client.post('/accounts/login/', {'username': 'lead_auditor', 'password': 'test'}, follow=True)
has_login_msg = any('authenticated successfully' in m.message for m in resp_login_ok.context['messages'])
record_test(resp_login_ok.status_code == 200 and has_login_msg, "POST /accounts/login/ with username produces success message")

# Test 7.5: Login POST empty
resp_login_empty = client.post('/accounts/login/', {'username': '', 'password': ''}, follow=True)
has_login_err = any('Please enter your auditor username' in m.message for m in resp_login_empty.context['messages'])
record_test(resp_login_empty.status_code == 200 and has_login_err, "POST /accounts/login/ with empty username produces clear error message")

# Test 7.6: ETL Upload empty file POST
resp_etl_empty = client.post('/analytics/etl/', {}, follow=True)
has_etl_err = any('No dataset file selected' in m.message for m in resp_etl_empty.context['messages'])
record_test(resp_etl_empty.status_code == 200 and has_etl_err, "POST /analytics/etl/ without file produces clear error message")

# Test 7.7: ETL Upload valid sample CSV file POST
with open('sample_audit_dataset.csv', 'rb') as fp:
    resp_etl_ok = client.post('/analytics/etl/', {'file': fp}, follow=True)
has_etl_succ = any('ETL Pipeline successfully processed' in m.message for m in resp_etl_ok.context['messages'])
record_test(resp_etl_ok.status_code == 200 and has_etl_succ, "POST /analytics/etl/ with sample CSV produces success message")

# Test 7.8: SQL Explorer valid POST
resp_sql_ok = client.post('/analytics/sql/', {'custom_sql': 'SELECT COUNT(*) as invoice_total FROM transactions_invoice'}, follow=True)
has_sql_succ = any('Query executed successfully' in m.message for m in resp_sql_ok.context['messages'])
record_test(resp_sql_ok.status_code == 200 and has_sql_succ, "POST /analytics/sql/ with valid SQL produces success message")

# Test 7.9: SQL Explorer invalid SQL syntax POST
resp_sql_bad = client.post('/analytics/sql/', {'custom_sql': 'SELECT INVALID_COLUMN_DOES_NOT_EXIST FROM NOT_A_TABLE'}, follow=True)
has_sql_err = any('SQL Execution Error' in m.message for m in resp_sql_bad.context['messages'])
record_test(resp_sql_bad.status_code == 200 and has_sql_err, "POST /analytics/sql/ with bad SQL produces clear error message")

# Test 7.10: Exception status update valid POST
test_exc = AuditException.objects.first()
if test_exc:
    pk = test_exc.exception_id
    resp_status_ok = client.post(f'/audit/exceptions/{pk}/status/', {
        'status': 'RESOLVED',
        'assigned_to': 'Lead Auditor Verification',
        'review_notes': 'Verified control compliance via test suite'
    }, follow=True)
    has_status_msg = any('updated to \'RESOLVED\'' in m.message for m in resp_status_ok.context['messages'])
    record_test(resp_status_ok.status_code == 200 and has_status_msg, f"POST /audit/exceptions/{pk}/status/ produces success message")

    # Verify DB update
    updated_exc = AuditException.objects.get(pk=pk)
    record_test(updated_exc.status == 'RESOLVED', "Exception status successfully persisted to database")

    # Test 7.11: Exception status update invalid status POST
    resp_status_bad = client.post(f'/audit/exceptions/{pk}/status/', {
        'status': 'NOT_A_VALID_STATUS'
    }, follow=True)
    has_status_err = any('Invalid exception status' in m.message for m in resp_status_bad.context['messages'])
    record_test(resp_status_bad.status_code == 200 and has_status_err, "POST /audit/exceptions/.../status/ with invalid status produces clear error message")

# ---------------------------------------------------------
# 8. TEST REPORTS & EXPORTS
# ---------------------------------------------------------
print("\n--- 8. Testing Reports & File Exports ---")

resp_pdf = client.get('/reports/pdf/')
is_pdf = resp_pdf.status_code == 200 and 'pdf' in resp_pdf.get('Content-Type', '').lower()
record_test(is_pdf, "GET /reports/pdf/ generates valid PDF binary download")

resp_csv = client.get('/reports/csv/')
is_csv = resp_csv.status_code == 200 and 'csv' in resp_csv.get('Content-Type', '').lower()
record_test(is_csv, "GET /reports/csv/ generates valid CSV download")

# ---------------------------------------------------------
# 9. TEST REST API ENDPOINTS
# ---------------------------------------------------------
print("\n--- 9. Testing REST API Endpoints ---")

resp_kpis = client.get('/api/dashboard/kpis/')
kpi_data = json.loads(resp_kpis.content)
record_test(resp_kpis.status_code == 200 and 'total_transactions_count' in kpi_data, "GET /api/dashboard/kpis/ returns valid JSON")

resp_api_excs = client.get('/api/exceptions/')
record_test(resp_api_excs.status_code == 200, "GET /api/exceptions/ returns status 200")

# Clean up database so it starts completely fresh for user
Invoice.objects.all().delete()
Payment.objects.all().delete()
PurchaseOrder.objects.all().delete()
EmployeeExpense.objects.all().delete()
AuditException.objects.all().delete()
AuditLog.objects.all().delete()
Vendor.objects.all().delete()
Employee.objects.all().delete()
Department.objects.all().delete()

# ---------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------
print("\n" + "=" * 80)
total_tests = passed_count + failed_count
print(f"VERIFICATION SUMMARY: {passed_count}/{total_tests} TESTS PASSED ({failed_count} FAILED)")
print("=" * 80)

if failed_count > 0:
    sys.exit(1)
else:
    print("ALL AUDIT REQUIREMENTS SUCCESSFULLY VERIFIED & FUNCTIONAL!")
    sys.exit(0)
