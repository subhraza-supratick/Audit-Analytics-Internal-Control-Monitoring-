from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_file_api, name='api_upload'),
    path('transactions/', views.list_transactions_api, name='api_transactions'),
    path('exceptions/', views.list_exceptions_api, name='api_exceptions'),
    path('exceptions/<int:pk>/', views.exception_detail_api, name='api_exception_detail'),
    path('exceptions/<int:pk>/status/', views.update_exception_status_api, name='api_exception_status'),
    path('vendors/<str:pk>/risk/', views.vendor_risk_api, name='api_vendor_risk'),
    path('dashboard/kpis/', views.dashboard_kpis_api, name='api_dashboard_kpis'),
    path('dashboard/trends/', views.dashboard_trends_api, name='api_dashboard_trends'),
    path('audit/run/', views.run_audit_api, name='api_audit_run'),
]
