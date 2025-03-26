from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('game/<int:game_id>/add_log/', views.add_log, name='add_log'),
    path('log/<int:log_id>/edit/', views.edit_log, name='edit_log'),
    path('log/<int:log_id>/delete/', views.delete_log, name='delete_log'),
    path('user/<int:user_id>/logs/', views.all_logs, name='all_logs'),
]
