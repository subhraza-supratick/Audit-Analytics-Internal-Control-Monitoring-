import random
from datetime import date, datetime, timedelta
from django.utils import timezone
from transactions.models import (
    Department, Employee, Vendor, PurchaseOrder, Invoice, Payment, EmployeeExpense, AuditException, AuditLog
)

# ---------------------------------------------------------------------------
# REAL-WORLD INDIAN SCENARIO:
# Company: Bharat Forge & Steel Manufacturing Pvt. Ltd. (Pune, Maharashtra)
# A mid-to-large Indian industrial manufacturer — realistic INR-scale data
# ---------------------------------------------------------------------------

def generate_synthetic_data(num_records=1000, clear_existing=True):
    if clear_existing:
        AuditLog.objects.all().delete()
        AuditException.objects.all().delete()
        Payment.objects.all().delete()
        Invoice.objects.all().delete()
        PurchaseOrder.objects.all().delete()
        EmployeeExpense.objects.all().delete()
        Employee.objects.all().delete()
        Vendor.objects.all().delete()
        Department.objects.all().delete()

    # ------------------------------------------------------------------
    # 1. Departments (realistic Indian industrial company structure)
    # ------------------------------------------------------------------
    dept_data = [
        ('DEP-FIN', 'Finance & Accounts',              'CC-101', 'Rajesh Sharma'),
        ('DEP-PROC', 'Purchase & Procurement',         'CC-202', 'Suresh Mehta'),
        ('DEP-IT',  'Information Technology',          'CC-303', 'Priya Iyer'),
        ('DEP-HR',  'Human Resources & Administration','CC-404', 'Kavita Desai'),
        ('DEP-PLT', 'Plant Operations & Production',   'CC-505', 'Ramesh Patil'),
    ]
    departments = []
    for d_id, name, cc, mgr in dept_data:
        dept = Department.objects.create(
            department_id=d_id, department_name=name, cost_center=cc, manager_name=mgr
        )
        departments.append(dept)

    # ------------------------------------------------------------------
    # 2. Employees (Indian names, realistic INR approval limits)
    # ------------------------------------------------------------------
    # Approval limits in INR: realistic for Indian corporate hierarchy
    emp_data = [
        # name,                        dept_id,    designation,                  limit_INR
        ("Ankit Malhotra",          "DEP-FIN",  "Vice President – Finance",          5000000),   # ₹50 Lakhs
        ("Sunita Kulkarni",         "DEP-PROC", "General Manager – Procurement",     2500000),   # ₹25 Lakhs
        ("Vikram Joshi",            "DEP-IT",   "Chief Technology Officer",          5000000),   # ₹50 Lakhs
        ("Meera Nair",              "DEP-HR",   "Director – Human Resources",        1500000),   # ₹15 Lakhs
        ("Arun Tiwari",             "DEP-PLT",  "Plant Manager",                     1000000),   # ₹10 Lakhs
        ("Deepa Krishnamurthy",     "DEP-FIN",  "Senior Accounts Payable Executive",  500000),  # ₹5 Lakhs
        ("Rohit Gupta",             "DEP-PROC", "Senior Purchase Officer",            800000),   # ₹8 Lakhs
        ("Neha Agarwal",            "DEP-IT",   "IT Infrastructure Manager",         1200000),   # ₹12 Lakhs
        ("Sanjay Yadav",            "DEP-PLT",  "Production Supervisor",              600000),   # ₹6 Lakhs
        ("Pooja Chaturvedi",        "DEP-FIN",  "Management Accountant",              700000),   # ₹7 Lakhs
    ]

    employees = []
    for i, (name, d_id, desig, limit) in enumerate(emp_data, 101):
        emp_id = f"EMP-{i}"
        dept = next(d for d in departments if d.department_id == d_id)
        emp = Employee.objects.create(
            employee_id=emp_id,
            name=name,
            department=dept,
            designation=desig,
            region=random.choice(['West India', 'North India', 'South India', 'East India']),
            manager_id='EMP-100',
            joining_date=date(2019, 4, 1) + timedelta(days=i * 45),
            approval_limit=limit,
            bank_account=f"HDFC{i:010d}",
            address=f"{100 + i}, Industrial Estate, MIDC, Pune - 4110{i:02d}",
            status='ACTIVE'
        )
        employees.append(emp)

    # ------------------------------------------------------------------
    # 3. Vendors (realistic Indian company names, types, GST-rated risk)
    # ------------------------------------------------------------------
    vendor_data = [
        # name,                                    type,                        risk,       bank_account
        ("Tata Technologies Ltd",                  "IT & Software Services",    "HIGH",    "ICIC0001001000000001"),
        ("Mahindra Logistics Pvt. Ltd.",           "Freight & Transportation",  "MEDIUM",  "SBIN0001002000000002"),
        ("Larsen & Toubro Construction",            "Civil & Infrastructure",    "CRITICAL","AXIS0001003000000003"),
        ("Bharat Electronics Supplies",            "Industrial Equipment",       "LOW",     "PNBP0001004000000004"),
        ("Godrej Facility Management Ltd",         "Facility & Housekeeping",   "LOW",     "CITI0001005000000005"),
        ("Navneet Office Solutions Pvt. Ltd.",     "Stationery & Office Supplies","LOW",   "HDFC0001006000000006"),
        ("SecureWatch Surveillance Corp.",         "Site Security Services",    "MEDIUM",  "KOTP0001007000000007"),
        ("MSEB Power Infrastructure Ltd.",         "Electricity & Utilities",   "LOW",     "UNIP0001008000000008"),
        ("AWS India Cloud Services Pvt. Ltd.",     "Cloud Hosting & DevOps",    "HIGH",    "DEUT0001009000000009"),
        # SHELL / CoI VENDOR — deliberately matches Employee EMP-106 (Deepa Krishnamurthy)
        ("Krishnamurthy Consultancy & Trading",    "Business Advisory",         "CRITICAL","HDFC0000000106"),  # same bank as EMP-106!
    ]
    vendors = []
    for i, (name, v_type, risk, bank) in enumerate(vendor_data, 501):
        v_id = f"VEND-{i}"
        addr = f"Plot {500 + i}, MIDC Industrial Area, Pune"
        if "Krishnamurthy" in name:
            # CoI: same bank account AND same home address as EMP-106 (Deepa Krishnamurthy)
            bank = employees[5].bank_account   # Deepa's bank account
            addr = employees[5].address        # Deepa's home address
        v = Vendor.objects.create(
            vendor_id=v_id,
            vendor_name=name,
            vendor_type=v_type,
            region=random.choice(['Maharashtra', 'Gujarat', 'Delhi NCR', 'Karnataka', 'Tamil Nadu']),
            bank_account=bank,
            address=addr,
            registration_date=date(2018, 4, 1) + timedelta(days=i),
            risk_category=risk,
            status='ACTIVE'
        )
        vendors.append(v)

    base_start_date = date(2025, 4, 1)   # Indian FY 2025-26

    # ------------------------------------------------------------------
    # 4. Baseline Financial Transactions (POs → Invoices → Payments)
    #    INR-scale amounts: ₹10,000 to ₹80% of employee approval limit
    # ------------------------------------------------------------------
    pos, invoices, payments = [], [], []
    po_counter  = 1000
    inv_counter = 5000
    pay_counter = 9000

    GST_RATES   = [0.05, 0.12, 0.18, 0.28]  # Indian GST slabs

    for i in range(1, num_records + 1):
        v = random.choice(vendors)
        e = random.choice(employees)
        d = e.department
        # Pick a weekday-only date in the FY (Mon-Fri) for clean baseline
        candidate = base_start_date + timedelta(days=random.randint(0, 330))
        while candidate.weekday() >= 5:   # skip Sat(5) and Sun(6)
            candidate += timedelta(days=1)
        po_date = candidate


        # Amount in INR — between ₹10,000 and 80% of approval limit
        amount = round(random.uniform(10000.0, float(e.approval_limit) * 0.80), 2)
        gst = round(amount * random.choice(GST_RATES), 2)

        po = PurchaseOrder.objects.create(
            po_id=f"PO-{po_counter}",
            vendor=v,
            employee=e,
            department=d,
            po_date=po_date,
            amount=amount,
            approval_status='APPROVED',
            approved_by=e.manager_id or 'SYSTEM'
        )
        po_counter += 1
        pos.append(po)

        inv_date = po_date + timedelta(days=random.randint(1, 7))
        inv = Invoice.objects.create(
            invoice_id=f"INV-{inv_counter}",
            vendor=v,
            po=po,
            invoice_date=inv_date,
            due_date=inv_date + timedelta(days=30),
            amount=amount,
            tax_amount=gst,
            payment_status='PAID',
            reference_no=f"GSTIN-{random.randint(10000, 99999)}"
        )
        inv_counter += 1
        invoices.append(inv)

        # Payment must be on a weekday during business hours (IST 9am-5pm)
        pay_base = inv_date + timedelta(days=random.randint(2, 25))
        while pay_base.weekday() >= 5:
            pay_base += timedelta(days=1)
        pay_dt = datetime.combine(pay_base, datetime.min.time()) \
                 + timedelta(hours=random.randint(9, 17))

        pay = Payment.objects.create(
            payment_id=f"PAY-{pay_counter}",
            invoice=inv,
            vendor=v,
            payment_date=timezone.make_aware(pay_dt),
            amount=amount,
            payment_method=random.choice(['NEFT', 'RTGS', 'IMPS', 'Cheque']),
            bank_account=v.bank_account,
            processed_by=e.name
        )
        pay_counter += 1
        payments.append(pay)

    # ------------------------------------------------------------------
    # 5. CONTROLLED AUDIT EXCEPTION SCENARIOS — all 11 rules, Indian scale
    # ------------------------------------------------------------------

    # Scenario 1 — Duplicate Invoice Detection
    # Same vendor issues two invoices with identical date, amount & reference
    dup_v   = vendors[0]   # Tata Technologies Ltd
    dup_po  = pos[0]
    dup_date = date(2025, 6, 14)
    dup_amt  = 1485000.00   # ₹14,85,000
    dup_ref  = "GSTIN-DUP-2501"
    Invoice.objects.create(
        invoice_id="INV-DUP-101", vendor=dup_v, po=dup_po,
        invoice_date=dup_date, due_date=dup_date + timedelta(days=30),
        amount=dup_amt, tax_amount=267300.00, payment_status='PAID', reference_no=dup_ref
    )
    Invoice.objects.create(
        invoice_id="INV-DUP-102", vendor=dup_v, po=dup_po,
        invoice_date=dup_date, due_date=dup_date + timedelta(days=30),
        amount=dup_amt, tax_amount=267300.00, payment_status='PAID', reference_no=dup_ref
    )

    # Scenario 2 — Duplicate Payment Detection
    target_inv = invoices[5]
    pay_t1 = timezone.make_aware(datetime(2025, 7, 2, 10, 30))
    pay_t2 = timezone.make_aware(datetime(2025, 7, 2, 10, 36))
    Payment.objects.create(payment_id="PAY-DUP-201", invoice=target_inv, vendor=target_inv.vendor,
        payment_date=pay_t1, amount=target_inv.amount, payment_method='RTGS',
        bank_account=target_inv.vendor.bank_account, processed_by='AP System')
    Payment.objects.create(payment_id="PAY-DUP-202", invoice=target_inv, vendor=target_inv.vendor,
        payment_date=pay_t2, amount=target_inv.amount, payment_method='RTGS',
        bank_account=target_inv.vendor.bank_account, processed_by='AP System')

    # Scenario 3 — Weekend Transaction Detection (Sunday 15 June 2025)
    wknd_date = date(2025, 6, 15)   # Sunday
    wknd_time = timezone.make_aware(datetime(2025, 6, 15, 14, 0))
    po_wk = PurchaseOrder.objects.create(
        po_id="PO-WK-301", vendor=vendors[1], employee=employees[1],
        department=employees[1].department, po_date=wknd_date,
        amount=4800000.00, approval_status='APPROVED', approved_by='EMERGENCY')
    inv_wk = Invoice.objects.create(
        invoice_id="INV-WK-301", vendor=vendors[1], po=po_wk,
        invoice_date=wknd_date, due_date=wknd_date + timedelta(days=30),
        amount=4800000.00, tax_amount=864000.00, payment_status='PAID',
        reference_no="REF-SUNDAY-URGNT")
    Payment.objects.create(
        payment_id="PAY-WK-301", invoice=inv_wk, vendor=vendors[1],
        payment_date=wknd_time, amount=4800000.00, payment_method='RTGS',
        bank_account=vendors[1].bank_account, processed_by='Weekend Admin')

    # Scenario 4 — After-hours Transaction (02:15 AM IST)
    aft_time = timezone.make_aware(datetime(2025, 8, 20, 2, 15))
    inv_ah = Invoice.objects.create(
        invoice_id="INV-AH-401", vendor=vendors[2], po=None,
        invoice_date=date(2025, 8, 19), due_date=date(2025, 9, 19),
        amount=6750000.00, tax_amount=1215000.00, payment_status='PAID',
        reference_no="REF-NIGHTPAY")
    Payment.objects.create(
        payment_id="PAY-AH-401", invoice=inv_ah, vendor=vendors[2],
        payment_date=aft_time, amount=6750000.00, payment_method='NEFT',
        bank_account=vendors[2].bank_account, processed_by='Overnight Script')

    # Scenario 5 — Round-Amount Transaction (₹50,00,000 exactly)
    po_rnd = PurchaseOrder.objects.create(
        po_id="PO-RND-501", vendor=vendors[2], employee=employees[2],
        department=employees[2].department, po_date=date(2025, 9, 1),
        amount=5000000.00, approval_status='APPROVED', approved_by=employees[2].name)
    Invoice.objects.create(
        invoice_id="INV-RND-501", vendor=vendors[2], po=po_rnd,
        invoice_date=date(2025, 9, 2), due_date=date(2025, 10, 2),
        amount=5000000.00, tax_amount=0.00, payment_status='PAID',
        reference_no="REF-RND-50LAK")

    # Scenario 6 — Approval-Threshold Violation
    # Sanjay Yadav (EMP-109, limit ₹6,00,000) approves ₹28,50,000 PO
    junior_emp = employees[8]   # Sanjay Yadav — ₹6L limit
    po_thr = PurchaseOrder.objects.create(
        po_id="PO-THR-601", vendor=vendors[3], employee=junior_emp,
        department=junior_emp.department, po_date=date(2025, 9, 10),
        amount=2850000.00, approval_status='APPROVED', approved_by=junior_emp.name)
    Invoice.objects.create(
        invoice_id="INV-THR-601", vendor=vendors[3], po=po_thr,
        invoice_date=date(2025, 9, 11), due_date=date(2025, 10, 11),
        amount=2850000.00, tax_amount=513000.00, payment_status='PENDING',
        reference_no="REF-OVERLIMIT")

    # Scenario 7 — Split Purchase Detection
    # Rohit Gupta (EMP-107, limit ₹8,00,000) issues 3 POs on same day totalling ₹24,50,000
    split_emp    = employees[6]    # Rohit Gupta
    split_vendor = vendors[4]      # Godrej Facility Management
    split_date   = date(2025, 9, 22)
    PurchaseOrder.objects.create(po_id="PO-SPLIT-701", vendor=split_vendor, employee=split_emp,
        department=split_emp.department, po_date=split_date, amount=980000.00,
        approval_status='APPROVED', approved_by=split_emp.name)
    PurchaseOrder.objects.create(po_id="PO-SPLIT-702", vendor=split_vendor, employee=split_emp,
        department=split_emp.department, po_date=split_date, amount=975000.00,
        approval_status='APPROVED', approved_by=split_emp.name)
    PurchaseOrder.objects.create(po_id="PO-SPLIT-703", vendor=split_vendor, employee=split_emp,
        department=split_emp.department, po_date=split_date, amount=990000.00,
        approval_status='APPROVED', approved_by=split_emp.name)

    # Scenario 8 — Employee-Vendor Conflict of Interest (CoI)
    # "Krishnamurthy Consultancy & Trading" (VEND-510) → same bank & address as
    # Deepa Krishnamurthy (EMP-106)
    coi_vendor = vendors[9]    # Krishnamurthy Consultancy & Trading
    coi_emp    = employees[5]  # Deepa Krishnamurthy
    coi_po = PurchaseOrder.objects.create(
        po_id="PO-COI-801", vendor=coi_vendor, employee=coi_emp,
        department=coi_emp.department, po_date=date(2025, 10, 5),
        amount=9500000.00, approval_status='APPROVED', approved_by=coi_emp.name)
    Invoice.objects.create(
        invoice_id="INV-COI-801", vendor=coi_vendor, po=coi_po,
        invoice_date=date(2025, 10, 6), due_date=date(2025, 11, 6),
        amount=9500000.00, tax_amount=1710000.00, payment_status='PAID',
        reference_no="REF-COI-SUSPICIOUS")

    # ------------------------------------------------------------------
    # 6. Employee Expenses (realistic Indian corporate expense categories)
    # ------------------------------------------------------------------
    exp_categories = [
        'Air Travel (Domestic)', 'Rail Travel', 'Client Entertainment',
        'Hotel Accommodation', 'Mobile & Internet Reimbursement',
        'Medical Reimbursement', 'Training & Conference', 'Office Supplies'
    ]
    exp_counter = 8000
    for _ in range(200):
        emp  = random.choice(employees)
        exp_date = base_start_date + timedelta(days=random.randint(0, 330))
        amt = round(random.uniform(2000.0, 50000.0), 2)
        EmployeeExpense.objects.create(
            expense_id=f"EXP-{exp_counter}",
            employee=emp, department=emp.department,
            expense_date=exp_date,
            category=random.choice(exp_categories),
            amount=amt,
            description=f"Business expense claim for project #{random.randint(100, 999)}",
            approval_status='APPROVED',
            approved_by=emp.manager_id or 'HOD'
        )
        exp_counter += 1

    # Scenario 9 — Employee Expense Anomaly (₹1,45,000 single entertainment claim)
    anom_emp = employees[3]   # Meera Nair
    EmployeeExpense.objects.create(
        expense_id="EXP-ANOM-901", employee=anom_emp, department=anom_emp.department,
        expense_date=date(2025, 10, 10), category='Client Entertainment',
        amount=145000.00,
        description="VIP client hospitality at Taj Hotel – Board-level client engagement dinner & resort",
        approval_status='APPROVED', approved_by=anom_emp.name
    )

    # Scenario 10 — Duplicate Employee Expense (₹32,000 submitted twice)
    dup_exp_emp  = employees[3]
    dup_exp_date = date(2025, 10, 12)
    EmployeeExpense.objects.create(
        expense_id="EXP-DUP-902", employee=dup_exp_emp, department=dup_exp_emp.department,
        expense_date=dup_exp_date, category='Training & Conference',
        amount=32000.00, description="Annual HR Leadership Summit – Delhi (Fee + Hotel + Travel)",
        approval_status='APPROVED', approved_by=dup_exp_emp.name
    )
    EmployeeExpense.objects.create(
        expense_id="EXP-DUP-903", employee=dup_exp_emp, department=dup_exp_emp.department,
        expense_date=dup_exp_date, category='Training & Conference',
        amount=32000.00, description="Annual HR Leadership Summit – Delhi (Fee + Hotel + Travel)",
        approval_status='APPROVED', approved_by=dup_exp_emp.name
    )

    print(f"[OK] Real-World Indian Scenario Data Generated!")
    print(f"     Company      : Bharat Forge & Steel Manufacturing Pvt. Ltd., Pune")
    print(f"     FY           : 2025-26 (April 2025 – March 2026)")
    print(f"     Baseline TXs : {num_records} transactions (INR scale)")
    print(f"     Exceptions   : 10 controlled audit violation scenarios injected")
