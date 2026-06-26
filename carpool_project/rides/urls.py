from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    path('rides/', views.ride_list, name='ride_list'),
    path('rides/create/', views.ride_create, name='ride_create'),
    path('rides/<int:pk>/', views.ride_detail, name='ride_detail'),
    path('rides/<int:pk>/join/', views.join_ride, name='join_ride'),
    path('rides/<int:pk>/leave/', views.leave_ride, name='leave_ride'),
    path('rides/<int:pk>/start/', views.start_ride, name='start_ride'),
    path('rides/<int:pk>/cancel/', views.cancel_ride, name='cancel_ride'),
    path('rides/<int:pk>/simulation/', views.ride_simulation, name='ride_simulation'),

    path('offices/', views.office_list, name='office_list'),
    path('offices/create/', views.office_create, name='office_create'),
    path('offices/<int:pk>/edit/', views.office_edit, name='office_edit'),
    path('offices/<int:pk>/delete/', views.office_delete, name='office_delete'),

    path('api/geocode/', views.api_geocode, name='api_geocode'),
    path('api/route/', views.api_route, name='api_route'),
    path('api/detect-city/', views.api_detect_city, name='api_detect_city'),
    path('api/compare-distances/', views.api_compare_distances, name='api_compare_distances'),
    path('api/rides/map/', views.api_rides_map, name='api_rides_map'),
]
