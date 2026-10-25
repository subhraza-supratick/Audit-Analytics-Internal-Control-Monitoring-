from django.urls import path
from . import views

urlpatterns = [
    path('', views.transaction_list, name='transaction_list'),
    path('seed/', views.seed_data_view, name='seed_data'),
    path('clear/', views.clear_data_view, name='clear_data'),
]
