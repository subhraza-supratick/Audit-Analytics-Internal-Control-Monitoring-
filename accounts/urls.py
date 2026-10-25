from django.urls import path
from . import views

urlpatterns = [
    path('switch-role/', views.switch_role, name='switch_role'),
    path('login/', views.login_view, name='login'),
]
