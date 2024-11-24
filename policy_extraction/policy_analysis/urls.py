# policy_analysis/urls.py


from django.urls import path
from . import views

# urlpatterns = [
#     path('', views.home_view, name='home'),
#     path('about/', views.about_view, name='about'),
#     path('contact/', views.contact_view, name='contact'),
#     path('login/', views.login_view, name='login'),
#     path('dashboard/', views.dashboard, name='dashboard'),
#     path('signup/', views.signup_view, name='signup'),  # Add this for signup
#     path('add_tracked_site/', views.add_tracked_site, name='add_tracked_site'),
#     path('delete-tracked-site/<int:pk>/', views.delete_tracked_site, name='delete_tracked_site'),
#     path('track_changes/<int:site_id>/', views.track_changes_view, name='track_changes'),
#     path('tracked-site/<int:pk>/', views.tracked_site_detail, name='tracked_site_detail'),
#     path('tracked_sites/', views.tracked_sites_view, name='tracked_sites'),
#     path('track_details/<int:tracked_site_id>/', views.track_details_view, name='track_details'),
#     path('add/', views.add_tracked_site, name='add_tracked_site'),
# ]

from django.contrib import admin
from django.urls import path
from policy_analysis import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.landing_page, name='landing_page'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add_url/', views.add_url_view, name='add_url_view'),
    path('logout/', views.logout_view, name='logout'),
    path('about/', views.about_view, name='about_view'),
    path('contact/', views.contact_view, name='contact_view'),
    path('site/<int:site_id>/', views.site_detail, name='site_detail'),
    path('site/<int:site_id>/scan/', views.scan_url_view, name='scan_url'),
    path('site/<int:pk>/edit/', views.edit_url_view, name='edit_url'),
    path('site/<int:pk>/delete/', views.delete_url_view, name='delete_url'),
]
