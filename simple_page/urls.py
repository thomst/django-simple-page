from django.urls import path
from . import views

urlpatterns = [
    path('', views.page, name='home'),
    path('<slug:slug>/', views.page, name='page'),
]