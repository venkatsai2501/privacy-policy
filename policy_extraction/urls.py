"""policy_extraction URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# policy_extraction/urls.py
from django.contrib import admin
from django.urls import path
from policy_analysis import views
from django.urls import path, include
urlpatterns = [
    path('admin/', admin.site.urls),  # Only include this line once
    path('', views.landing_page, name='landing_page'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add_url/', views.add_url_view, name='add_url_view'),
    path('logout/', views.logout_view, name='logout'),
    path('about/', views.about_view, name='about_view'),
    path('contact/', views.about_view, name='contact_view'),
    # path('scan_url/<int:site_id>/', views.scan_url_view, name='scan_url'),
    # path('edit_url/<int:pk>/', views.edit_url_view, name='edit_url'),
    # path('delete_url/<int:pk>/', views.delete_url_view, name='delete_url'),
    path('site/<int:site_id>/', views.site_detail, name='site_detail'),
    path('site/<int:site_id>/scan/', views.scan_url_view, name='scan_url'),
    path('site/<int:pk>/edit/', views.edit_url_view, name='edit_url'),
    path('site/<int:pk>/delete/', views.delete_url_view, name='delete_url'),
    path('test_search/', include('test_search.urls')),
    path('mark_notification_as_read/<int:notification_id>/', views.mark_notification_as_read, name='mark_notification_as_read'),
    path('toggle_auto_scan/<int:site_id>/', views.toggle_auto_scan, name='toggle_auto_scan'),
]