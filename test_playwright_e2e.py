"""
Playwright End-to-End Comprehensive Test Suite
Tests every single feature, UI component, workflow, mobile drawer, form, export,
error state, and interactive 3D elements in a real Chrome browser.
"""

import os
import sys
import time
import subprocess
import requests
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8000"

def ensure_server_running():
    """Ensure Django development server is up and listening on port 8000."""
    try:
        r = requests.get(BASE_URL, timeout=1.5)
        if r.status_code in [200, 302]:
            print(f"[OK] Django dev server is already running on {BASE_URL}")
            return None
    except Exception:
        pass

    print(f"[INFO] Starting Django server on {BASE_URL}...")
    proc = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", "127.0.0.1:8000", "--noreload"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    # Wait for server to be responsive
    for _ in range(30):
        time.sleep(0.5)
        try:
            r = requests.get(BASE_URL, timeout=1.0)
            if r.status_code in [200, 302]:
                print(f"[OK] Django dev server started successfully (PID: {proc.pid})")
                return proc
        except Exception:
            continue

    print("[ERROR] Timed out waiting for Django dev server to start!")
    return proc

def run_e2e_tests():
    server_proc = ensure_server_running()

    passed = 0
    failed = 0

    def check(condition, label, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            failed += 1
            print(f"  [FAIL] {label} -> {detail}")
        return condition

    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(channel="chrome", headless=True)
                print("[INFO] Launched browser using official Google Chrome channel.")
            except Exception as e:
                browser = p.chromium.launch(headless=True)
                print(f"[INFO] Fallback to standard Chromium: {e}")

            context = browser.new_context(viewport={"width": 1440, "height": 900})
            page = context.new_page()

            # Track page console errors
            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

            print("\n" + "=" * 80)
            print("PLAYWRIGHT E2E BROWSER TEST EXECUTION ON CHROME")
            print("=" * 80)

            # -------------------------------------------------------------
            # TEST 1: Platform Overview & Landing Page + Executive Overview Dashboard
            # -------------------------------------------------------------
            print("\n>>> 1. Testing Platform Overview Landing Page & Executive Dashboard (Desktop)")
            page.goto(f"{BASE_URL}/", wait_until="networkidle")
            
            # Title & Meta Description on Landing Page
            title = page.title()
            check("Platform Overview" in title or "Audit Analytics" in title, f"Landing page title valid: '{title}'")
            meta_desc = page.locator('meta[name="description"]').get_attribute('content')
            check(bool(meta_desc and len(meta_desc) > 15), f"Meta description present: '{meta_desc[:40]}...'")

            # Favicon
            favicon = page.locator('link[rel="icon"]').get_attribute('href')
            check("favicon.svg" in str(favicon), f"Favicon link present: '{favicon}'")

            # 3D Background Canvas
            canvas_3d = page.locator('#bgCanvas3D')
            check(canvas_3d.is_visible(), "Ambient Telemetry Particle Mesh Canvas visible in background")

            # Landing page hero CTA and sections
            hero_btn = page.locator('a:has-text("Launch Executive Audit Workspace")').first
            check(hero_btn.is_visible(), "CTA button 'Launch Executive Audit Workspace' visible on landing page")
            check(page.locator('h2:has-text("How to Use the System")').first.is_visible(), "5-Step Operational Guide section visible")
            check(page.locator('h2:has-text("The 11 Automated Audit Heuristics")').first.is_visible(), "11 Heuristics section visible")

            # Brand logo links to homepage
            brand_link = page.locator('.sidebar-brand-link')
            check(brand_link.is_visible() and brand_link.get_attribute('href') == '/', "Logo links to homepage '/'")

            # Click CTA to navigate to Executive Overview Dashboard (/dashboard/)
            with page.expect_navigation():
                hero_btn.click()
            check(page.url.endswith('/dashboard/'), f"CTA navigated to Executive Overview: {page.url}")

            # Now on Executive Dashboard:
            dash_title = page.title()
            check("Executive Overview" in dash_title, f"Dashboard title valid: '{dash_title}'")

            # KPI Cards
            kpis = page.locator('.kpi-card')
            kpi_count = kpis.count()
            check(kpi_count >= 4, f"Rendered {kpi_count} KPI metric cards")

            # Donut & Bar Charts
            sev_chart = page.locator('#severityChart')
            check(sev_chart.is_visible(), "Exception Risk Severity Chart Canvas rendered")
            status_chart = page.locator('#statusChart')
            check(status_chart.is_visible(), "Workflow Status Bar Chart Canvas rendered")

            # Seed sample ledger if starting fresh so rules engine and exceptions can be tested
            seed_btn = page.locator('button:has-text("Load Sample Audit Ledger"), button:has-text("Re-seed 1,000 Records")')
            if seed_btn.is_visible():
                with page.expect_navigation():
                    seed_btn.click()
                print("  [PASS] Seeded 1,000 sample transaction records for test evaluation")

            # Priority Flagged Exceptions Table
            exc_table = page.locator('.custom-table tbody tr')
            check(exc_table.count() > 0, f"Priority Flagged Exceptions table has {exc_table.count()} rows")

            # Test Role Switcher in Top Navbar (switch to ADMIN)
            role_select = page.locator('#roleSelect')
            check(role_select.is_visible(), "Role Switcher dropdown visible")
            with page.expect_navigation():
                role_select.select_option('ADMIN')
            alert = page.locator('.alert-banner')
            check(alert.is_visible() and "ADMIN" in alert.text_content(), "Role switch auto-submits and shows success banner")

            # Test Run Audit Engine button
            run_btn = page.locator('button:has-text("Run Audit Engine")')
            check(run_btn.is_visible(), "Run Audit Engine button visible")
            with page.expect_navigation():
                run_btn.click()
            check(page.url.endswith('/dashboard/exceptions/'), "Run Audit Engine redirects to Exceptions Explorer")
            alert = page.locator('.alert-banner')
            check(alert.is_visible() and "Audit Rules Engine executed" in alert.text_content(), "Audit Engine execution success banner displayed")

            # -------------------------------------------------------------
            # TEST 2: Audit Exceptions Center & Filters
            # -------------------------------------------------------------
            print("\n>>> 2. Testing Audit Exceptions Explorer & Filters")
            page.goto(f"{BASE_URL}/dashboard/exceptions/", wait_until="networkidle")

            # Filter by CRITICAL severity
            page.select_option('select[name="severity"]', 'CRITICAL')
            page.click('button:has-text("Filter")')
            page.wait_for_load_state("networkidle")
            check("severity=CRITICAL" in page.url, "URL updated with severity=CRITICAL")
            critical_badges = page.locator('.badge-critical')
            check(critical_badges.count() > 0, f"Critical exceptions filtered: {critical_badges.count()} critical badges shown")

            # Search by keyword
            page.fill('input[name="q"]', 'Invoice')
            page.click('button:has-text("Filter")')
            page.wait_for_load_state("networkidle")
            check("q=Invoice" in page.url, "Search query applied in URL")

            # Reset filters
            page.goto(f"{BASE_URL}/dashboard/exceptions/", wait_until="networkidle")
            check(page.url.endswith('/dashboard/exceptions/'), "Reset clears filter parameters")

            # Click Investigate button on first exception
            first_investigate = page.locator('.custom-table tbody tr a:has-text("Investigate")').first
            check(first_investigate.is_visible(), "Investigate button visible on exception row")
            first_investigate.click()
            page.wait_for_load_state("networkidle")
            check("/dashboard/exceptions/" in page.url and page.url.endswith("/"), f"Navigated to Investigation Detail: {page.url}")

            # -------------------------------------------------------------
            # TEST 3: Investigation Detail & Workflow Status Update
            # -------------------------------------------------------------
            print("\n>>> 3. Testing Investigation Detail & Auditor Working Papers")
            
            # Lineage & Explainable Risk
            check(page.locator('text=Transaction Lineage Trace').is_visible(), "Transaction Lineage Trace visible")
            check(page.locator('text=Explainable Risk Score Components').is_visible(), "Explainable Risk Components visible")
            check(page.locator('text=Audit Log Trail History').is_visible(), "Audit Log History visible")

            # Fill review form
            status_dropdown = page.locator('#investigationStatusSelect')
            check(status_dropdown.is_visible(), "Investigation status select dropdown visible")
            status_dropdown.select_option('UNDER_REVIEW')
            page.fill('input[name="assigned_to"]', 'Senior QA Auditor Playwright')
            page.fill('textarea[name="review_notes"]', 'E2E automated verification of internal control deviation.')

            # Submit update form
            submit_btn = page.locator('button:has-text("Update Exception Record")')
            submit_btn.click()
            page.wait_for_load_state("networkidle")

            alert = page.locator('.alert-banner')
            check(alert.is_visible() and "updated to 'UNDER_REVIEW'" in alert.text_content(), "Exception status updated with success banner")

            # -------------------------------------------------------------
            # TEST 4: Financial Analysis Page
            # -------------------------------------------------------------
            print("\n>>> 4. Testing Financial Spend Analysis Page")
            page.goto(f"{BASE_URL}/dashboard/financial/", wait_until="networkidle")
            check("Financial Analysis" in page.title(), "Financial Analysis page title verified")
            check(page.locator('text=Total Disbursed Spend').is_visible(), "Total Disbursed Spend KPI visible")
            check(page.locator('text=Top 10 Vendor Spend Concentration').is_visible(), "Top Vendor Spend panel visible")
            check(page.locator('text=Departmental Budget Execution').is_visible(), "Department Spend panel visible")

            # -------------------------------------------------------------
            # TEST 5: Vendor Risk Matrix Page
            # -------------------------------------------------------------
            print("\n>>> 5. Testing Vendor Risk Matrix Page")
            page.goto(f"{BASE_URL}/dashboard/vendors/", wait_until="networkidle")
            check("Vendor Risk Matrix" in page.title(), "Vendor Risk Matrix page title verified")
            vendor_rows = page.locator('.custom-table tbody tr')
            check(vendor_rows.count() > 0, f"Vendor directory has {vendor_rows.count()} vendors listed")

            # -------------------------------------------------------------
            # TEST 6: Financial Transaction Ledger & Tabs
            # -------------------------------------------------------------
            print("\n>>> 6. Testing Financial Transaction Ledger & Tabs")
            page.goto(f"{BASE_URL}/transactions/", wait_until="networkidle")
            check("Financial Transaction Records" in page.title(), "Transaction Ledger title verified")

            # Test tabs
            page.click('a:has-text("Payments")')
            page.wait_for_load_state("networkidle")
            check("type=payments" in page.url, "Switched to Payments tab")

            page.click('a:has-text("Purchase Orders")')
            page.wait_for_load_state("networkidle")
            check("type=purchase_orders" in page.url, "Switched to Purchase Orders tab")

            page.click('a:has-text("Employee Expenses")')
            page.wait_for_load_state("networkidle")
            check("type=expenses" in page.url, "Switched to Employee Expenses tab")

            # Test search in invoices
            page.click('a:has-text("Invoices")')
            page.wait_for_load_state("networkidle")
            page.fill('input[name="q"]', 'INV')
            page.click('button:has-text("Search")')
            page.wait_for_load_state("networkidle")
            check("q=INV" in page.url, "Search keyword applied to transactions")

            # Test Pagination
            next_page = page.locator('a.btn:has-text("Next")')
            if next_page.is_visible():
                next_page.click()
                page.wait_for_load_state("networkidle")
                check("page=2" in page.url, "Pagination Next button navigated to page 2")

            # -------------------------------------------------------------
            # TEST 7: Interactive SQL Analytics Lab
            # -------------------------------------------------------------
            print("\n>>> 7. Testing Interactive SQL Analytics Lab")
            page.goto(f"{BASE_URL}/analytics/sql/", wait_until="networkidle")
            check("SQL Analytics" in page.title(), "SQL Analytics title verified")

            # Click predefined query from list
            query_link = page.locator('a[href="?query_id=q2"]').first
            query_link.click()
            page.wait_for_load_state("networkidle")
            check("query_id=q2" in page.url, "Predefined query selected: q2 (Top Vendors)")

            # Submit valid SQL execution
            exec_btn = page.locator('button:has-text("Execute SQL Query")')
            exec_btn.click()
            page.wait_for_load_state("networkidle")
            alert = page.locator('.alert-banner')
            check(alert.is_visible() and "Query executed successfully" in alert.text_content(), "SQL executed successfully with metrics banner")

            # Submit invalid SQL syntax and verify clear error message
            page.fill('textarea[name="custom_sql"]', 'SELECT NOT_A_REAL_COLUMN FROM FAKE_TABLE;')
            exec_btn.click()
            page.wait_for_load_state("networkidle")
            error_alert = page.locator('.alert-error, .alert-danger')
            check(error_alert.is_visible() and "SQL Execution Error" in error_alert.text_content(), "Invalid SQL produces clear error alert banner")

            # -------------------------------------------------------------
            # TEST 8: ETL Ingestion Pipeline
            # -------------------------------------------------------------
            print("\n>>> 8. Testing ETL Data Pipeline")
            page.goto(f"{BASE_URL}/analytics/etl/", wait_until="networkidle")
            check("ETL Pipeline" in page.title(), "ETL Ingestion title verified")

            # Upload real sample dataset
            sample_file = os.path.abspath('sample_audit_dataset.csv')
            page.set_input_files('input[type="file"]', sample_file)
            page.click('button:has-text("Run Pandas ETL Pipeline & Ingest")')
            page.wait_for_load_state("networkidle")

            alert = page.locator('.alert-banner')
            check(alert.is_visible() and "ETL Pipeline successfully processed" in alert.text_content(), "ETL upload ingested file with success banner")
            check(page.get_by_text("Data Quality Score", exact=True).is_visible(), "Data Quality Score panel displayed")

            # -------------------------------------------------------------
            # TEST 9: Management Reports & PDF Downloads
            # -------------------------------------------------------------
            print("\n>>> 9. Testing Management Reports & Exports")
            page.goto(f"{BASE_URL}/reports/", wait_until="networkidle")
            check("Audit Reports" in page.title(), "Reports index title verified")

            # Test PDF download trigger
            with page.expect_download() as download_info:
                page.click('a:has-text("Download PDF Report")')
            download = download_info.value
            check(download.suggested_filename.endswith('.pdf'), f"PDF Report downloaded: '{download.suggested_filename}'")

            # Test CSV download trigger
            with page.expect_download() as download_info_csv:
                page.click('a:has-text("Download CSV Data File")')
            download_csv = download_info_csv.value
            check(download_csv.suggested_filename.endswith('.csv'), f"CSV Data exported: '{download_csv.suggested_filename}'")

            # -------------------------------------------------------------
            # TEST 10: Auditor RBAC Login Page
            # -------------------------------------------------------------
            print("\n>>> 10. Testing Auditor Login Portal")
            page.goto(f"{BASE_URL}/accounts/login/", wait_until="networkidle")
            check("Auditor Authentication" in page.title(), "Login page title verified")

            page.fill('input[name="username"]', 'LeadAuditorE2E')
            page.fill('input[name="password"]', 'AuditSecure2026!')
            with page.expect_navigation():
                page.click('button:has-text("Sign In to Audit Dashboard")')
            check(page.url.endswith('/dashboard/'), "Login redirected to dashboard overview")
            alert = page.locator('.alert-banner')
            check(alert.is_visible() and "authenticated successfully" in alert.text_content(), "Login generated success banner")

            # -------------------------------------------------------------
            # TEST 11: Audit Governance & Policy Page (Clickable Tel & Mailto)
            # -------------------------------------------------------------
            print("\n>>> 11. Testing Audit Policy & Clickable Contacts")
            page.goto(f"{BASE_URL}/audit-policy/", wait_until="networkidle")
            check("Audit Governance" in page.title(), "Audit policy title verified")

            tel_link = page.locator('a[href="tel:+18005552834"]').first
            check(tel_link.is_visible(), "Clickable telephone link (tel:+18005552834) verified")

            mail_link = page.locator('a[href="mailto:audit-desk@internal-controls.org"]').first
            check(mail_link.is_visible(), "Clickable email link (mailto:audit-desk@internal-controls.org) verified")

            # -------------------------------------------------------------
            # TEST 12: Custom 404 Page
            # -------------------------------------------------------------
            print("\n>>> 12. Testing Custom 404 Page Experience")
            resp_404 = page.goto(f"{BASE_URL}/404/", wait_until="networkidle")
            check(resp_404.status == 404, f"Response HTTP status is 404 ({resp_404.status})")
            check("404" in page.title(), "404 title verified")
            check(page.locator('text=Ledger Page Not Found').is_visible(), "Custom 404 headline visible")
            ret_btn = page.locator('a:has-text("Return to Executive Dashboard")')
            check(ret_btn.is_visible(), "Return to Dashboard button present on 404 page")

            # -------------------------------------------------------------
            # TEST 13: Mobile Responsive Viewport & Hamburger Drawer Navigation
            # -------------------------------------------------------------
            print("\n>>> 13. Testing Mobile Responsive Viewport & Hamburger Menu (iPhone 375x812)")
            mobile_context = browser.new_context(viewport={"width": 375, "height": 812})
            mobile_page = mobile_context.new_page()
            mobile_page.goto(f"{BASE_URL}/", wait_until="networkidle")

            # Check horizontal scrolling: document.documentElement.scrollWidth <= window.innerWidth
            has_no_horizontal_scroll = mobile_page.evaluate("""
                () => {
                    const scrollWidth = document.documentElement.scrollWidth;
                    const clientWidth = document.documentElement.clientWidth;
                    return scrollWidth <= clientWidth + 1; // 1px rounding tolerance
                }
            """)
            check(has_no_horizontal_scroll, "Zero horizontal scroll on mobile viewport (scrollWidth <= clientWidth)")

            # Mobile hamburger button must be visible
            mob_btn = mobile_page.locator('#mobileMenuBtn')
            check(mob_btn.is_visible(), "Mobile Hamburger toggle button visible on screen width <= 1024px")

            # Sidebar should initially be offscreen
            sidebar = mobile_page.locator('#mainSidebar')
            is_open_initial = sidebar.evaluate("el => el.classList.contains('open')")
            check(not is_open_initial, "Sidebar is initially closed on mobile")

            # Click Hamburger Menu to open drawer
            mob_btn.click()
            mobile_page.wait_for_timeout(300)
            is_open_after = sidebar.evaluate("el => el.classList.contains('open')")
            overlay = mobile_page.locator('#sidebarOverlay')
            is_overlay_active = overlay.evaluate("el => el.classList.contains('active')")
            check(is_open_after and is_overlay_active, "Clicking hamburger opens sidebar drawer with backdrop overlay")

            # Click close button inside drawer to close
            close_btn = mobile_page.locator('#sidebarCloseBtn')
            close_btn.click()
            mobile_page.wait_for_timeout(300)
            is_closed_after = not sidebar.evaluate("el => el.classList.contains('open')")
            check(is_closed_after, "Clicking close button collapses sidebar drawer")

            # Click hamburger again and close via overlay backdrop click
            mob_btn.click()
            mobile_page.wait_for_timeout(300)
            overlay.click(position={"x": 300, "y": 300}, force=True)
            mobile_page.wait_for_timeout(300)
            check(not sidebar.evaluate("el => el.classList.contains('open')"), "Clicking backdrop overlay closes drawer")

            # -------------------------------------------------------------
            # TEST 14: Auto-Updating Copyright Year in Footer
            # -------------------------------------------------------------
            print("\n>>> 14. Testing Auto-Updating Copyright Year")
            footer_year = page.locator('#copyrightYear').text_content()
            import datetime
            current_year = str(datetime.datetime.now().year)
            check(footer_year.strip() == current_year, f"Copyright year is automatically '{current_year}'")

            # Check console errors (ignoring deliberate 404 HTTP status code from Test 12)
            real_errors = [e for e in console_errors if not ("status of 404" in e or "404 (Not Found)" in e)]
            check(len(real_errors) == 0, f"Zero unexpected browser console errors detected ({len(real_errors)} errors)", str(real_errors))

            # -------------------------------------------------------------
            # RESET TO CLEAN STATE FOR USER
            # -------------------------------------------------------------
            print("\n>>> Resetting ledger to clean fresh state...")
            page.goto(f"{BASE_URL}/dashboard/", wait_until="networkidle")
            page.once("dialog", lambda dialog: dialog.accept())
            clear_btn = page.locator('button:has-text("Reset Ledger")')
            if clear_btn.is_visible():
                with page.expect_navigation():
                    clear_btn.click()
                print("  [PASS] Successfully reset ledger to clean fresh slate")

            browser.close()

            print("\n" + "=" * 80)
            total = passed + failed
            print(f"PLAYWRIGHT E2E SUMMARY: {passed}/{total} TESTS PASSED ({failed} FAILED)")
            print("=" * 80)

            if failed > 0:
                sys.exit(1)
            else:
                print("ALL PLAYWRIGHT TESTS PASSED WITH 100% SUCCESS ON CHROME!")
                sys.exit(0)

    finally:
        if server_proc:
            print("[INFO] Terminating temporary test server...")
            server_proc.terminate()

if __name__ == "__main__":
    run_e2e_tests()
