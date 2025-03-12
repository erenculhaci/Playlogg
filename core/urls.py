from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('profile/', views.user_profile, name='profile'),
    path('add_game/', views.add_game, name='add_game'),
    path('unfavorite/<int:game_id>/', views.unfavorite_game, name='unfavorite_game'),

    path('edit_game/<int:game_id>/', views.edit_game, name='edit_game'),
    path('delete_game/<int:game_id>/', views.delete_game, name='delete_game'),
    path('like_game/<int:game_id>/', views.like_game, name='like_game'),
    path('add_comment/<int:game_id>/', views.add_comment, name='add_comment'),
    path('edit_comment/<int:comment_id>/', views.edit_comment, name='edit_comment'),
    path('delete_comment/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('game_detail/<int:game_id>/', views.game_detail, name='game_detail'),
    path('logout/', views.user_logout, name='logout'),
    path('like_comment/<int:comment_id>/', views.like_comment, name='like_comment'),
    path('game/<int:game_id>/add_log/', views.add_log, name='add_log'),
    path('log/<int:log_id>/edit/', views.edit_log, name='edit_log'),
    path('log/<int:log_id>/delete/', views.delete_log, name='delete_log'),
    path('user/<int:user_id>/logs/', views.all_logs, name='all_logs'),  # Yeni URL

]
