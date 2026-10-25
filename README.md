# Audit Analytics & Internal Control Monitoring System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0%2B-092E20.svg?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-150458.svg?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Scikit-Learn](https://img.shields.io/badge/ML-Isolation%20Forest-F7931E.svg?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL%20%7C%20SQLite-336791.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An enterprise-grade audit analytics and continuous control monitoring platform that automates financial exception detection, risk scoring, and investigation workflows across procurement, accounts payable, and employee expense lifecycles.

---

## 1. Executive Summary & Business Scenario

### Business Problem
Internal audit and financial controllership teams in mid-to-large enterprises face significant risks of control circumvention, billing anomalies, duplicate disbursements, and unapproved spend across thousands of monthly procurement transactions. Manual sample testing typically covers less than 5% of transactional volume, leaving high-exposure anomalies undetected.

### Business Objective
Build a continuous, automated audit analytics engine that:
1. **Performs 100% Transaction Testing** across purchase orders, vendor invoices, payment vouchers, and employee expense claims.
2. **Detects Rule Violations & Complex Anomalies** using deterministic audit rules combined with unsupervised machine learning (Isolation Forest).
3. **Assigns Explainable Risk Scores (0–100)** to prioritize auditor review based on exposure, severity, and historical patterns.
4. **Provides an End-to-End Investigation Workflow** with role-based access control (RBAC), immutable audit logs, and PDF/CSV reporting.

### Simulated Enterprise Profile
- **Company:** Bharat Forge & Steel Manufacturing Pvt. Ltd. (Pune, Maharashtra)
- **Currency & Scale:** Indian Rupee (INR / ₹) with realistic enterprise authorization thresholds (₹5L to ₹50L).
- **Core Entities:** Departments, Authorized Signatories, Registered Vendors, Purchase Orders, Tax Invoices, Bank Payments, and Expense Claims.

---

## 2. System Architecture

```
                       FINANCIAL DATA SOURCES
                (CSV / XLSX / JSON ERP Export Batches)
                                  │
                                  ▼
               ┌──────────────────────────────────────┐
               │         DJANGO INGESTION & ETL       │
               ├──────────────────────────────────────┤
               │ • File Schema & Type Validation      │
               │ • Deduplication & Cleaning (Pandas)  │
               │ • Relational Integrity Enforcement   │
               └──────────────────┬───────────────────┘
                                  │
                                  ▼
               ┌──────────────────────────────────────┐
               │     NORMALIZED TRANSACTIONAL STORE   │
               │        (PostgreSQL / SQLite)         │
               └──────────────────┬───────────────────┘
                                  │
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
       ┌──────────────────────┐       ┌──────────────────────┐
       │   SQL & RULE AUDIT   │       │  MACHINE LEARNING    │
       │   DETECTION ENGINE   │       │   ANOMALY ENGINE     │
       ├──────────────────────┤       ├──────────────────────┤
       │ • Duplicate Invoices │       │ • Isolation Forest   │
       │ • Split Purchases    │       │ • Multi-Dimensional  │
       │ • Threshold Bypasses │       │   Feature Vectors    │
       │ • Timing Anomalies   │       │ • Unsupervised Novel │
       │ • Vendor Outliers    │       │   Pattern Detection  │
       └──────────┬───────────┘       └──────────┬───────────┘
                  │                               │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
               ┌──────────────────────────────────────┐
               │    EXPLAINABLE RISK SCORING ENGINE   │
               ├──────────────────────────────────────┤
               │ • Rule Weight + Value + ML Severity  │
               │ • Tiered: Low / Med / High / Critical│
               │ • Exposure Calculation (₹ INR)      │
               └──────────────────┬───────────────────┘
                                  │
                                  ▼
               ┌──────────────────────────────────────┐
               │    INVESTIGATION & AUDIT WORKFLOW    │
               ├──────────────────────────────────────┤
               │ • State Machine: Open → In Review →  │
               │   Resolved / False Positive          │
               │ • Immutable Audit Logs & Revisions   │
               │ • Role-Based Access Control (RBAC)   │
               │ • Executive BI Dashboards & PDF Export│
               └──────────────────────────────────────┘
```

---

## 3. Core Audit Rules & Detection Modules

| Rule ID | Audit Check | Detection Logic | Severity |
|---|---|---|---|
| **R-01** | **Duplicate Invoices** | Detects matching or near-duplicate invoices (same vendor, date, amount, or invoice reference). | **Critical** |
| **R-02** | **Duplicate Payments** | Identifies multiple payment disbursements against the same invoice or identical vendor-amount pairings within 7 days. | **Critical** |
| **R-03** | **Split Purchases** | Flags multiple purchase orders issued to the same vendor within 48 hours that individually fall under approval limits but collectively exceed them. | **High** |
| **R-04** | **Threshold Bypass** | Compares purchase orders and expense claims against the employee's formal delegation of authority (DOA) limit. | **High** |
| **R-05** | **Weekend / After-Hours** | Identifies transactions recorded on Saturdays, Sundays, or outside standard operating hours (8:00 PM – 7:00 AM). | **Medium** |
| **R-06** | **Round Amount Anomaly** | Flags large disbursements that are exact multiples of ₹50,000 or ₹1,00,000 without corresponding breakdown details. | **Medium** |
| **R-07** | **Unusual Vendor Volume** | Identifies rapid expenditure surges (>300% of 90-day moving average) for dormant or newly registered vendors. | **High** |
| **R-08** | **Duplicate Employee Expenses**| Detects repeated claims by the same employee with identical amount, category, and date. | **Medium** |
| **R-09** | **Vendor-Employee Conflict** | Identifies matching bank account numbers, tax identifiers, or contact details between employees and registered vendors. | **Critical** |

---

## 4. Explainable Risk Scoring Framework

Rather than treating anomaly detection as an opaque black box, every audit exception is evaluated using an **explainable multi-factor scoring formula (0–100)**:

$$\text{Risk Score} = w_r \cdot S_{\text{rule}} + w_v \cdot S_{\text{value}} + w_f \cdot S_{\text{frequency}} + w_m \cdot S_{\text{ML}}$$

- **Rule Severity ($S_{\text{rule}}$):** Baseline score derived from internal control failure criticality (0 to 40).
- **Transaction Value Exposure ($S_{\text{value}}$):** Scaled logarithmic impact based on transaction monetary value (0 to 30).
- **Historical Frequency ($S_{\text{frequency}}$):** Penalty applied if the vendor or employee has repeated prior violations (0 to 15).
- **Unsupervised ML Anomaly ($S_{\text{ML}}$):** Isolation Forest contamination distance score (0 to 15).

### Risk Classification Tiers
- **Critical (81–100):** Immediate audit investigation required; potential material exposure or intentional bypass.
- **High (61–80):** High-priority review within 48 hours; unauthorized threshold or duplicate billing.
- **Medium (31–60):** Operational non-compliance or timing irregularity for routine reconciliation.
- **Low (0–30):** Minor deviations or informational audit flags.

---

## 5. Django Application Structure

```
Audit_Analytics_System/
├── accounts/                  # Authentication, User Models & RBAC Permissions
├── analytics/                 # ETL Pipelines, Data Quality Audits & SQL Analytics
├── audit_engine/              # Rule Definitions, Isolation Forest ML & Risk Scorer
├── audit_project/             # Django Settings, URL Configuration & WSGI/ASGI
├── dashboard/                 # Views, KPI Aggregations & Analytical Endpoints
├── reports/                   # Automated PDF & CSV Management Report Generators
├── transactions/              # Core Domain Models (PO, Invoice, Payment, Expense)
├── static/                    # CSS Design Tokens, Charting JS & Dashboard UI
├── templates/                 # Jinja/Django Responsive Templates & Modal Forms
├── generate_sample_data.py    # Industrial Synthetic Data Generator (INR / ₹)
├── run_audit.py               # Batch Audit Pipeline CLI Runner
├── run_tests.py               # Comprehensive Test Suite Runner
├── db.sqlite3                 # Local Pre-Seeded Development Database
├── requirements.txt           # Python Package Dependencies
└── README.md                  # Project Documentation
```

---

## 6. Role-Based Access Control (RBAC)

The application implements four distinct user tiers:
1. **Audit Administrator:** Full system configuration, rule weight adjustments, user provisioning, and raw data re-indexing.
2. **Senior Auditor:** Exception assignment, investigation notes, state transitions (`OPEN` → `UNDER REVIEW` → `RESOLVED` / `FALSE POSITIVE`), and report generation.
3. **Data Analyst:** Batch data ingestion (ETL upload), ad-hoc SQL query execution, and exploratory analytics.
4. **Executive / Viewer:** Read-only access to summarized KPI cards, financial exposure charts, and high-level audit summaries.

---

## 7. REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/dashboard/kpis/` | Summary metrics: total spend, exception counts, exposure value, and risk distribution. |
| `GET` | `/api/transactions/` | Paginated list of financial transactions with filtering by department and date range. |
| `GET` | `/api/exceptions/` | List of flagged audit exceptions filtered by severity, status, or rule type. |
| `GET` | `/api/exceptions/<id>/` | Detailed drill-down for a specific exception including rule logic and evidence. |
| `PATCH` | `/api/exceptions/<id>/status/` | Update exception state (`UNDER REVIEW`, `RESOLVED`, `FALSE POSITIVE`) with auditor note. |
| `POST` | `/api/audit/run/` | Trigger on-demand batch audit execution across all unanalyzed records. |

---

## 8. Installation & Setup

### Prerequisites
- Python 3.10 or higher
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/subhraza-supratick/Audit-Analytics-Internal-Control-Monitoring-.git
cd Audit-Analytics-Internal-Control-Monitoring-
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup & Migrations
```bash
python manage.py migrate
```

### 5. Seed Synthetic Enterprise Data & Run Audit Rules
```bash
# Run data seeding script (generates ~1,000 realistic transactions with injected anomalies)
python manage.py shell -c "from transactions.seed_data import generate_synthetic_data; generate_synthetic_data()"

# Execute the audit engine to detect anomalies and compute risk scores
python run_audit.py
```

### 6. Start Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## 9. Running Verification & Automated Tests

To run the complete automated test suite covering ETL validation, audit rules, risk scoring, and RBAC:

```bash
python run_tests.py
```
Or with Django test runner:
```bash
python manage.py test
```

---

## 10. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
