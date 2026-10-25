from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages
from django.http import JsonResponse
from analytics.sql_queries import SQL_AUDIT_QUERIES
from analytics.etl import process_etl_upload

def sql_explorer_view(request):
    selected_query_id = request.GET.get('query_id', 'q1')
    raw_sql = request.POST.get('custom_sql', '')
    
    selected_item = next((q for q in SQL_AUDIT_QUERIES if q['id'] == selected_query_id), SQL_AUDIT_QUERIES[0])
    
    query_to_run = raw_sql if raw_sql else selected_item['sql']
    results = []
    columns = []
    error_msg = None
    exec_time_ms = 0

    if query_to_run:
        import time
        start_time = time.time()
        try:
            with connection.cursor() as cursor:
                cursor.execute(query_to_run)
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    results = cursor.fetchall()
            exec_time_ms = round((time.time() - start_time) * 1000, 2)
            if request.method == 'POST':
                messages.success(request, f"Query executed successfully in {exec_time_ms} ms ({len(results)} rows returned).")
        except Exception as e:
            error_msg = str(e)
            messages.error(request, f"SQL Execution Error: {error_msg}")

    return render(request, 'analytics/sql_explorer.html', {
        'queries': SQL_AUDIT_QUERIES,
        'selected_item': selected_item,
        'query_to_run': query_to_run,
        'columns': columns,
        'results': results[:100], # Limit to 100 for display
        'result_count': len(results),
        'error_msg': error_msg,
        'exec_time_ms': exec_time_ms
    })

def etl_upload_view(request):
    report = None
    if request.method == 'POST':
        if request.FILES.get('file'):
            file_obj = request.FILES['file']
            report = process_etl_upload(file_obj)
            if 'error' in report:
                messages.error(request, f"ETL Ingestion Error: {report['error']}")
            else:
                messages.success(request, f"ETL Pipeline successfully processed '{file_obj.name}' with {report['data_quality_score']}% Data Quality Score! Ingested {report['records_persisted']} records.")
        else:
            messages.error(request, "No dataset file selected. Please choose a CSV or Excel (.xlsx) file to upload.")

    return render(request, 'analytics/etl_upload.html', {
        'report': report
    })
