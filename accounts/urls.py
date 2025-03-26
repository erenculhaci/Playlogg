from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.user_profile, name='profile'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('delete_profile/', views.delete_profile, name='delete_profile'),
    path('view_profile/<int:user_id>/', views.view_profile, name='view_profile'),

    # Email verification URLs
    path('verify/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('resend-verification-profile/', views.resend_verification_from_profile, name='resend_verification_profile'),
    # Password reset URLs
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset-confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('change-password/', views.change_password, name='change_password'),

    path('update-email/', views.update_email, name='update_email'),
    path('confirm-email-update/<uidb64>/<token>/', views.confirm_email_update, name='confirm_email_update'),
]
