from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page_view, name='landing_page'),
    path('dashboard/', views.executive_overview, name='dashboard_overview'),
    path('dashboard/overview/', views.executive_overview, name='dashboard_overview_alias'),
    path('dashboard/financial/', views.financial_analysis, name='dashboard_financial'),
    path('dashboard/exceptions/', views.audit_exceptions_view, name='dashboard_exceptions'),
    path('dashboard/exceptions/<int:pk>/', views.investigation_detail, name='investigation_detail'),
    path('dashboard/vendors/', views.vendor_risk_matrix, name='vendor_risk_matrix'),
    path('interview-prep/', views.interview_prep_view, name='interview_prep'),
    path('404/', views.custom_404_view, name='preview_404'),
    path('audit-policy/', views.audit_policy_view, name='audit_policy'),
]
