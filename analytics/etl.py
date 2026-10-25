import pandas as pd
import numpy as np
from datetime import datetime, date
from django.db import transaction
from transactions.models import Invoice, Vendor, PurchaseOrder, Department, Employee
from audit_engine.rules import run_all_audit_rules

def process_etl_upload(file_obj, persist_to_db=True):
    """
    Pandas-based ETL data ingestion & quality validation engine.
    Extracts, cleans, validates, and loads financial transaction data.
    Automatically ingests valid records into database and triggers audit rules engine.
    """
    try:
        # 1. Extraction
        if file_obj.name.endswith('.csv'):
            df = pd.read_csv(file_obj)
        elif file_obj.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_obj)
        elif file_obj.name.endswith('.json'):
            df = pd.read_json(file_obj)
        else:
            return {'error': 'Unsupported file format. Please upload CSV, XLSX, or JSON.'}

        initial_rows = len(df)
        if initial_rows == 0:
            return {'error': 'Uploaded file is empty.'}

        missing_values = int(df.isnull().sum().sum())
        
        # 2. Data Cleaning - Deduplicate
        df_clean = df.drop_duplicates(subset=['invoice_id'] if 'invoice_id' in df.columns else None)
        duplicates_removed = initial_rows - len(df_clean)

        # 3. Schema Validation
        required_cols = {'invoice_id', 'amount', 'vendor_id'}
        missing_cols = required_cols - set(df_clean.columns)
        if missing_cols:
            return {'error': f'Schema Validation Failed! Missing required columns: {", ".join(missing_cols)}'}

        # 4. Type conversions & cleaning
        df_clean['amount'] = pd.to_numeric(df_clean['amount'], errors='coerce').fillna(0.0)
        df_clean = df_clean[df_clean['amount'] > 0]

        valid_rows = len(df_clean)
        rejected_rows = initial_rows - valid_rows
        total_ingested_val = round(float(df_clean['amount'].sum()), 2)

        # 5. Database Ingestion & Persistence
        records_saved = 0
        if persist_to_db and valid_rows > 0:
            with transaction.atomic():
                for _, row in df_clean.iterrows():
                    inv_id = str(row['invoice_id']).strip()
                    vend_id = str(row['vendor_id']).strip()
                    vend_name = str(row.get('vendor_name', vend_id)).strip() if 'vendor_name' in row else vend_id
                    
                    # Ensure vendor exists
                    vendor_obj, _ = Vendor.objects.get_or_create(
                        vendor_id=vend_id,
                        defaults={
                            'vendor_name': vend_name or f"Vendor {vend_id}",
                            'vendor_type': 'General Supplier',
                            'region': 'North India',
                            'bank_account': f'SBIN{np.random.randint(10000000, 99999999)}',
                            'registration_date': date.today()
                        }
                    )

                    # Parse dates
                    inv_date = date.today()
                    if 'invoice_date' in row and pd.notna(row['invoice_date']):
                        try:
                            inv_date = pd.to_datetime(row['invoice_date']).date()
                        except:
                            inv_date = date.today()

                    due_date = inv_date
                    if 'due_date' in row and pd.notna(row['due_date']):
                        try:
                            due_date = pd.to_datetime(row['due_date']).date()
                        except:
                            due_date = inv_date

                    tax_val = float(row.get('tax_amount', 0.0)) if pd.notna(row.get('tax_amount')) else 0.0
                    status_val = str(row.get('payment_status', 'PAID')).strip().upper()
                    if status_val not in ['PAID', 'PENDING', 'CANCELLED']:
                        status_val = 'PAID'

                    po_obj = None
                    if 'po_id' in row and pd.notna(row['po_id']):
                        po_str = str(row['po_id']).strip()
                        po_obj = PurchaseOrder.objects.filter(po_id=po_str).first()

                    Invoice.objects.update_or_create(
                        invoice_id=inv_id,
                        defaults={
                            'vendor': vendor_obj,
                            'po': po_obj,
                            'invoice_date': inv_date,
                            'due_date': due_date,
                            'amount': float(row['amount']),
                            'tax_amount': tax_val,
                            'payment_status': status_val,
                            'reference_no': str(row.get('description', ''))[:50]
                        }
                    )
                    records_saved += 1

            # 6. Automatically trigger Audit Engine to re-evaluate anomalies
            audit_summary = run_all_audit_rules()
        else:
            audit_summary = {'total_exceptions': 0, 'high_critical_count': 0}

        report = {
            'file_name': file_obj.name,
            'initial_rows': initial_rows,
            'valid_rows': valid_rows,
            'rejected_rows': rejected_rows,
            'duplicates_removed': duplicates_removed,
            'missing_values_repaired': missing_values,
            'records_persisted': records_saved,
            'data_quality_score': round((valid_rows / max(1, initial_rows)) * 100, 1),
            'total_value': total_ingested_val,
            'audit_exceptions_flagged': audit_summary.get('total_exceptions', 0),
            'critical_exceptions': audit_summary.get('high_critical_count', 0)
        }
        return report
    except Exception as e:
        return {'error': f'ETL Pipeline Processing Error: {str(e)}'}
