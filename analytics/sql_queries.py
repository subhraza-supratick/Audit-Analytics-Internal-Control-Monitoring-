SQL_AUDIT_QUERIES = [
    {
        "id": "q1",
        "title": "Duplicate Invoice Detection Query",
        "category": "Audit Controls",
        "description": "Identifies vendors issuing multiple invoices on the exact same date for identical dollar amounts.",
        "sql": """SELECT vendor_id, invoice_date, amount, COUNT(*) AS invoice_count
FROM transactions_invoice
GROUP BY vendor_id, invoice_date, amount
HAVING COUNT(*) > 1;"""
    },
    {
        "id": "q2",
        "title": "Top Vendors by Total Payment Volume",
        "category": "Vendor Intelligence",
        "description": "Aggregates total disbursements per vendor ranked in descending order to identify concentration risk.",
        "sql": """SELECT v.vendor_name, v.vendor_type, SUM(p.amount) AS total_paid, COUNT(p.payment_id) AS payment_count
FROM transactions_payment p
JOIN transactions_vendor v ON p.vendor_id = v.vendor_id
GROUP BY v.vendor_id, v.vendor_name, v.vendor_type
ORDER BY total_paid DESC
LIMIT 10;"""
    },
    {
        "id": "q3",
        "title": "Purchase Orders Exceeding Delegated Approval Limits",
        "category": "Internal Control Violations",
        "description": "Finds purchase orders where amount exceeds the authorized spending threshold of the issuing employee.",
        "sql": """SELECT po.po_id, e.name AS employee_name, e.approval_limit, po.amount AS po_amount, (po.amount - e.approval_limit) AS excess_amount
FROM transactions_purchaseorder po
JOIN transactions_employee e ON po.employee_id = e.employee_id
WHERE po.amount > e.approval_limit
ORDER BY excess_amount DESC;"""
    },
    {
        "id": "q4",
        "title": "Window Function: Departmental Spend Ranking (CTEs & DENSE_RANK)",
        "category": "Advanced Analytics",
        "description": "Uses Common Table Expressions (CTEs) and Window Functions to rank vendor spend within each department.",
        "sql": """WITH DepartmentVendorSpend AS (
    SELECT d.department_name, v.vendor_name, SUM(po.amount) AS total_dept_vendor_spend
    FROM transactions_purchaseorder po
    JOIN transactions_department d ON po.department_id = d.department_id
    JOIN transactions_vendor v ON po.vendor_id = v.vendor_id
    GROUP BY d.department_name, v.vendor_name
)
SELECT department_name, vendor_name, total_dept_vendor_spend,
       DENSE_RANK() OVER (PARTITION BY department_name ORDER BY total_dept_vendor_spend DESC) AS spend_rank
FROM DepartmentVendorSpend
ORDER BY department_name, spend_rank;"""
    },
    {
        "id": "q5",
        "title": "Weekend Payment Execution Audit",
        "category": "Timing & Fraud Risk",
        "description": "Flags payments processed on Saturdays and Sundays which pose elevated internal control risk.",
        "sql": """SELECT p.payment_id, p.payment_date, p.amount, v.vendor_name, p.processed_by
FROM transactions_payment p
JOIN transactions_vendor v ON p.vendor_id = v.vendor_id
WHERE strftime('%w', p.payment_date) IN ('0', '6')
ORDER BY p.payment_date DESC;"""
    },
    {
        "id": "q6",
        "title": "Employee-Vendor Conflict of Interest (Address / Bank Match)",
        "category": "Fraud & Ethics",
        "description": "Cross-references employee master data against vendor master data to detect matching street addresses or bank accounts.",
        "sql": """SELECT e.employee_id, e.name AS employee_name, v.vendor_id, v.vendor_name, e.address, e.bank_account
FROM transactions_employee e
JOIN transactions_vendor v ON e.address = v.address OR e.bank_account = v.bank_account;"""
    },
    {
        "id": "q7",
        "title": "Split Purchase Detection (Same Employee, Same Vendor, Same Day)",
        "category": "Internal Control Violations",
        "description": "Detects multiple purchase orders generated on the same day for the same vendor that collectively exceed authorization limits.",
        "sql": """SELECT po.employee_id, e.name AS employee_name, po.vendor_id, po.po_date,
       SUM(po.amount) AS combined_day_amount, COUNT(po.po_id) AS split_po_count, e.approval_limit
FROM transactions_purchaseorder po
JOIN transactions_employee e ON po.employee_id = e.employee_id
GROUP BY po.employee_id, po.vendor_id, po.po_date
HAVING COUNT(po.po_id) > 1 AND SUM(po.amount) > e.approval_limit;"""
    },
    {
        "id": "q8",
        "title": "Large Perfectly Rounded Invoices ($10,000+)",
        "category": "Anomaly Detection",
        "description": "Filters invoices with perfectly rounded monetary amounts (divisible by $5,000) for forensic review.",
        "sql": """SELECT i.invoice_id, v.vendor_name, i.invoice_date, i.amount
FROM transactions_invoice i
JOIN transactions_vendor v ON i.vendor_id = v.vendor_id
WHERE i.amount >= 10000.00 AND (CAST(i.amount AS INT) % 5000) = 0
ORDER BY i.amount DESC;"""
    },
    {
        "id": "q9",
        "title": "Department Expense Breakdown & Exception Rates",
        "category": "Executive Governance",
        "description": "Calculates total expenditure and percentage of flagged audit exceptions per department.",
        "sql": """SELECT d.department_name, SUM(e.amount) AS total_expense, COUNT(e.expense_id) AS total_claims
FROM transactions_employeeexpense e
JOIN transactions_department d ON e.department_id = d.department_id
GROUP BY d.department_name
ORDER BY total_expense DESC;"""
    },
    {
        "id": "q10",
        "title": "High & Critical Severity Exception Summary",
        "category": "Audit Controls",
        "description": "Lists all unresolved high and critical audit exceptions along with total financial exposure.",
        "sql": """SELECT exception_id, transaction_id, exception_type, severity, risk_score, amount, status
FROM transactions_auditexception
WHERE severity IN ('HIGH', 'CRITICAL')
ORDER BY risk_score DESC;"""
    }
]
