from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='index'),
    path('profile/', views.profile, name='profile'),
    path('history/', views.history, name='history'),
    path('upload/', views.upload, name='upload'),
    path('result/<int:pk>/', views.result, name='result'),
]
