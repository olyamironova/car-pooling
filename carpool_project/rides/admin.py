from django.contrib import admin
from .models import UserProfile, Office, Ride, RidePassenger, RideRating


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'city', 'phone', 'rating', 'total_rides']
    list_filter = ['role', 'city']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'city']


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'address', 'lat', 'lon', 'is_active', 'created_at']
    list_filter = ['city', 'is_active']
    search_fields = ['name', 'city', 'address']
    list_editable = ['is_active']


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = ['id', 'driver', 'office', 'departure_city', 'departure_time',
                    'status', 'available_seats', 'route_distance_km']
    list_filter = ['status', 'departure_city', 'office']
    search_fields = ['driver__username', 'departure_address']
    readonly_fields = ['route_distance_km', 'route_duration_min', 'simulation_progress']


@admin.register(RidePassenger)
class RidePassengerAdmin(admin.ModelAdmin):
    list_display = ['ride', 'passenger', 'status', 'joined_at']
    list_filter = ['status']
    search_fields = ['passenger__username', 'ride__id']


@admin.register(RideRating)
class RideRatingAdmin(admin.ModelAdmin):
    list_display = ['ride', 'rater', 'rated_user', 'score', 'created_at']
    list_filter = ['score']
