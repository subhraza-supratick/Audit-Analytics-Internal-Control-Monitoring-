from django.urls import path
from . import views

urlpatterns = [
    path('run/', views.run_audit_view, name='run_audit'),
    path('exceptions/<int:exception_id>/status/', views.update_exception_status, name='update_exception_status'),
]
