from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.search_company, name='search_company'),
    path('', views.test_page, name='test_page'),
]
