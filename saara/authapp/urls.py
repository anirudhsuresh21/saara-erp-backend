"""
URL configuration for auth app
"""
from django.urls import path
from . import views

urlpatterns = [
    path('auth/login/', views.supabase_login, name='supabase_login'),
    path('auth/register/', views.supabase_register, name='supabase_register'),
    path('auth/logout/', views.supabase_logout, name='supabase_logout'),
    path('auth/user/', views.get_current_user, name='get_current_user'),
    path('auth/refresh/', views.refresh_token, name='refresh_token'),
    path('auth/allowed-domains/', views.get_allowed_domains, name='get_allowed_domains'),
    
    # Development-only endpoint (disabled in production)
    path('auth/dev-login/', views.dev_login, name='dev_login'),
]
