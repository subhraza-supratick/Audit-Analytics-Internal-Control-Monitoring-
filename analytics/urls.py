from django.urls import path
from . import views

urlpatterns = [
    path('sql/', views.sql_explorer_view, name='sql_explorer'),
    path('etl/', views.etl_upload_view, name='etl_upload'),
]
