from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('add_comment/<int:game_id>/', views.add_comment, name='add_comment'),
    path('edit_comment/<int:comment_id>/', views.edit_comment, name='edit_comment'),
    path('delete_comment/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('like_comment/<int:comment_id>/', views.like_comment, name='like_comment'),
]
