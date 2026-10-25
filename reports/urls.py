from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_index, name='reports_index'),
    path('pdf/', views.export_pdf_report, name='export_pdf'),
    path('csv/', views.export_csv_report, name='export_csv'),
]
