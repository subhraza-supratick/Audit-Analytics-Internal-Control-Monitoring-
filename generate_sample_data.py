import os
import pandas as pd
import numpy as np
from datetime import date, timedelta

os.makedirs('static/samples', exist_ok=True)

# Generate realistic Indian Enterprise Audit Dataset
rows = [
    # Normal Invoices
    {"invoice_id": "INV-2026-8001", "vendor_id": "VEND-501", "vendor_name": "Tata Communications Ltd", "po_id": "PO-1001", "invoice_date": "2026-03-01", "due_date": "2026-03-31", "amount": 145000.00, "tax_amount": 26100.00, "payment_status": "PAID", "description": "Cloud & MPLS Network Infrastructure Q1"},
    {"invoice_id": "INV-2026-8002", "vendor_id": "VEND-502", "vendor_name": "Infosys BPO Solutions", "po_id": "PO-1002", "invoice_date": "2026-03-02", "due_date": "2026-04-01", "amount": 89000.00, "tax_amount": 16020.00, "payment_status": "PAID", "description": "Customer Support Operations Mar 2026"},
    {"invoice_id": "INV-2026-8003", "vendor_id": "VEND-503", "vendor_name": "L&T Heavy Engineering", "po_id": "PO-1003", "invoice_date": "2026-03-03", "due_date": "2026-04-02", "amount": 320000.00, "tax_amount": 57600.00, "payment_status": "PAID", "description": "Facility Maintenance & HVAC Works"},
    {"invoice_id": "INV-2026-8004", "vendor_id": "VEND-504", "vendor_name": "Reliance Logistics Hub", "po_id": "PO-1004", "invoice_date": "2026-03-04", "due_date": "2026-04-03", "amount": 76500.00, "tax_amount": 13770.00, "payment_status": "PAID", "description": "Inter-State Freight & Delivery Services"},
    {"invoice_id": "INV-2026-8005", "vendor_id": "VEND-505", "vendor_name": "Wipro Enterprise Services", "po_id": "PO-1005", "invoice_date": "2026-03-05", "due_date": "2026-04-04", "amount": 112000.00, "tax_amount": 20160.00, "payment_status": "PAID", "description": "IT Security Audit & Compliance Retainer"},

    # RED FLAG 1: Duplicate Invoices (Exact duplicate amount & vendor on same/consecutive date)
    {"invoice_id": "INV-2026-8010", "vendor_id": "VEND-506", "vendor_name": "Apex Tech Services Mumbai", "po_id": "PO-1006", "invoice_date": "2026-03-10", "due_date": "2026-04-09", "amount": 185000.00, "tax_amount": 33300.00, "payment_status": "PAID", "description": "Server Virtualization Upgrades Part 1"},
    {"invoice_id": "INV-2026-8011", "vendor_id": "VEND-506", "vendor_name": "Apex Tech Services Mumbai", "po_id": "PO-1006", "invoice_date": "2026-03-10", "due_date": "2026-04-09", "amount": 185000.00, "tax_amount": 33300.00, "payment_status": "PAID", "description": "Server Virtualization Upgrades Part 1 (Duplicate Bill)"},

    # RED FLAG 2: Split Invoices just below ₹50,000 threshold (Structured structuring)
    {"invoice_id": "INV-2026-8020", "vendor_id": "VEND-507", "vendor_name": "Bharat Stationery & Supplies", "po_id": "PO-1007", "invoice_date": "2026-03-12", "due_date": "2026-04-11", "amount": 49200.00, "tax_amount": 8856.00, "payment_status": "PAID", "description": "Office Supplies Batch A"},
    {"invoice_id": "INV-2026-8021", "vendor_id": "VEND-507", "vendor_name": "Bharat Stationery & Supplies", "po_id": "PO-1007", "invoice_date": "2026-03-12", "due_date": "2026-04-11", "amount": 49800.00, "tax_amount": 8964.00, "payment_status": "PAID", "description": "Office Supplies Batch B"},
    {"invoice_id": "INV-2026-8022", "vendor_id": "VEND-507", "vendor_name": "Bharat Stationery & Supplies", "po_id": "PO-1007", "invoice_date": "2026-03-12", "due_date": "2026-04-11", "amount": 49500.00, "tax_amount": 8910.00, "payment_status": "PAID", "description": "Office Supplies Batch C"},

    # RED FLAG 3: Round Number Suspicious Transactions
    {"invoice_id": "INV-2026-8030", "vendor_id": "VEND-508", "vendor_name": "Zenith Consulting Pune", "po_id": "PO-1008", "invoice_date": "2026-03-15", "due_date": "2026-04-14", "amount": 500000.00, "tax_amount": 90000.00, "payment_status": "PAID", "description": "Management Strategy Advisory Services"},
    {"invoice_id": "INV-2026-8031", "vendor_id": "VEND-508", "vendor_name": "Zenith Consulting Pune", "po_id": "PO-1008", "invoice_date": "2026-03-16", "due_date": "2026-04-15", "amount": 1000000.00, "tax_amount": 180000.00, "payment_status": "PENDING", "description": "Executive Leadership Coaching Program"},

    # RED FLAG 4: High Value Outlier Transaction
    {"invoice_id": "INV-2026-8040", "vendor_id": "VEND-509", "vendor_name": "Mahindra Power Systems", "po_id": "PO-1009", "invoice_date": "2026-03-18", "due_date": "2026-04-17", "amount": 4750000.00, "tax_amount": 855000.00, "payment_status": "PAID", "description": "Industrial Diesel Generator Backup Installation"},

    # RED FLAG 5: Benford's Law Deviations (Concentration on digits 7, 8, 9)
    {"invoice_id": "INV-2026-8051", "vendor_id": "VEND-510", "vendor_name": "Delta Electronics Bangalore", "po_id": "PO-1010", "invoice_date": "2026-03-20", "due_date": "2026-04-19", "amount": 98400.00, "tax_amount": 17712.00, "payment_status": "PAID", "description": "Semiconductor Component Kits"},
    {"invoice_id": "INV-2026-8052", "vendor_id": "VEND-510", "vendor_name": "Delta Electronics Bangalore", "po_id": "PO-1010", "invoice_date": "2026-03-21", "due_date": "2026-04-20", "amount": 89200.00, "tax_amount": 16056.00, "payment_status": "PAID", "description": "Testing & Calibration Kits"},
    {"invoice_id": "INV-2026-8053", "vendor_id": "VEND-510", "vendor_name": "Delta Electronics Bangalore", "po_id": "PO-1010", "invoice_date": "2026-03-22", "due_date": "2026-04-21", "amount": 78900.00, "tax_amount": 14202.00, "payment_status": "PAID", "description": "Optoelectronic Sensory Units"},

    # Additional Routine Invoices
    {"invoice_id": "INV-2026-8061", "vendor_id": "VEND-501", "vendor_name": "Tata Communications Ltd", "po_id": "PO-1001", "invoice_date": "2026-03-23", "due_date": "2026-04-22", "amount": 128000.00, "tax_amount": 23040.00, "payment_status": "PAID", "description": "Fiber Optic Line Bandwidth Expansion"},
    {"invoice_id": "INV-2026-8062", "vendor_id": "VEND-502", "vendor_name": "Infosys BPO Solutions", "po_id": "PO-1002", "invoice_date": "2026-03-24", "due_date": "2026-04-23", "amount": 94500.00, "tax_amount": 17010.00, "payment_status": "PAID", "description": "Quarterly Helpdesk Operations Support"},
    {"invoice_id": "INV-2026-8063", "vendor_id": "VEND-503", "vendor_name": "L&T Heavy Engineering", "po_id": "PO-1003", "invoice_date": "2026-03-25", "due_date": "2026-04-24", "amount": 215000.00, "tax_amount": 38700.00, "payment_status": "PENDING", "description": "Structural Steel Fabrications"},
]

df = pd.DataFrame(rows)

# Save to CSV
csv_path_root = "sample_audit_dataset.csv"
csv_path_static = "static/samples/sample_audit_dataset.csv"
df.to_csv(csv_path_root, index=False)
df.to_csv(csv_path_static, index=False)

# Save to Excel XLSX
xlsx_path_root = "sample_audit_dataset.xlsx"
xlsx_path_static = "static/samples/sample_audit_dataset.xlsx"
df.to_excel(xlsx_path_root, index=False, engine='openpyxl')
df.to_excel(xlsx_path_static, index=False, engine='openpyxl')

print(f"Generated {len(df)} sample audit records successfully in CSV and XLSX formats.")
