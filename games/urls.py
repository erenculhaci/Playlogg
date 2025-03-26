from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('add_game/', views.add_game, name='add_game'),
    path('unfavorite/<int:game_id>/', views.unfavorite_game, name='unfavorite_game'),
    path('edit_game/<int:game_id>/', views.edit_game, name='edit_game'),
    path('delete_game/<int:game_id>/', views.delete_game, name='delete_game'),
    path('like_game/<int:game_id>/', views.like_game, name='like_game'),
    path('game_detail/<int:game_id>/', views.game_detail, name='game_detail'),
]
