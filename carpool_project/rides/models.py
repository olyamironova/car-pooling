from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import math


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Администратор'),
        ('driver', 'Водитель'),
        ('passenger', 'Пассажир'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='passenger')
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    home_address = models.CharField(max_length=255, blank=True)
    home_lat = models.FloatField(null=True, blank=True)
    home_lon = models.FloatField(null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)
    car_model = models.CharField(max_length=100, blank=True)
    car_plate = models.CharField(max_length=20, blank=True)
    car_seats = models.IntegerField(default=4)
    rating = models.FloatField(default=5.0)
    total_rides = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"

    def is_driver(self):
        return self.role == 'driver'

    def is_passenger(self):
        return self.role == 'passenger'

    def is_admin(self):
        return self.role == 'admin' or self.user.is_staff


class Office(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=500)
    city = models.CharField(max_length=100)
    lat = models.FloatField()
    lon = models.FloatField()
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to='offices/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['city', 'name']

    def __str__(self):
        return f"{self.name} ({self.city})"


class Ride(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Запланирована'),
        ('active', 'В пути'),
        ('completed', 'Завершена'),
        ('cancelled', 'Отменена'),
    ]

    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rides_as_driver')
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name='rides')

    departure_address = models.CharField(max_length=500)
    departure_lat = models.FloatField()
    departure_lon = models.FloatField()
    departure_city = models.CharField(max_length=100, blank=True)

    departure_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    available_seats = models.IntegerField(default=3)
    total_seats = models.IntegerField(default=3)

    comment = models.TextField(blank=True)

    route_distance_km = models.FloatField(null=True, blank=True)
    route_duration_min = models.FloatField(null=True, blank=True)
    route_geometry = models.TextField(blank=True)

    current_lat = models.FloatField(null=True, blank=True)
    current_lon = models.FloatField(null=True, blank=True)
    simulation_progress = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-departure_time']

    def __str__(self):
        return f"Поездка {self.driver.username} -> {self.office.name} в {self.departure_time}"

    def get_filled_seats(self):
        return self.passengers.filter(status='confirmed').count()

    def get_free_seats(self):
        return self.available_seats - self.get_filled_seats()

    def can_join(self, user):
        """Check if user can join this ride"""
        if self.status != 'scheduled':
            return False, "Поездка уже началась или завершена"
        if self.driver == user:
            return False, "Вы являетесь водителем этой поездки"
        if self.passengers.filter(passenger=user).exists():
            return False, "Вы уже присоединились к этой поездке"
        if self.get_free_seats() <= 0:
            return False, "Нет свободных мест"

        try:
            profile = user.profile
            if profile.city and self.departure_city:
                if profile.city.lower() != self.departure_city.lower():
                    user_city_key = self._detect_city_key(profile.city)
                    ride_city_key = self._detect_city_key(self.departure_city)
                    if user_city_key and ride_city_key and user_city_key != ride_city_key:
                        return False, f"Ваш город ({profile.city}) не совпадает с городом отправления поездки ({self.departure_city})"
        except Exception:
            pass

        return True, "OK"

    def _detect_city_key(self, city_name):
        city_map = {
            'москва': 'moscow', 'moscow': 'moscow',
            'санкт-петербург': 'spb', 'спб': 'spb', 'питер': 'spb',
            'saint-petersburg': 'spb', 'st. petersburg': 'spb',
            'новосибирск': 'novosibirsk', 'novosibirsk': 'novosibirsk',
            'екатеринбург': 'ekb', 'yekaterinburg': 'ekb',
        }
        return city_map.get(city_name.lower().strip())


class RidePassenger(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтверждён'),
        ('rejected', 'Отклонён'),
        ('cancelled', 'Отменён'),
    ]

    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='passengers')
    passenger = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rides_as_passenger')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    pickup_address = models.CharField(max_length=500, blank=True)
    pickup_lat = models.FloatField(null=True, blank=True)
    pickup_lon = models.FloatField(null=True, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('ride', 'passenger')

    def __str__(self):
        return f"{self.passenger.username} в поездке {self.ride.id}"


class RideRating(models.Model):
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='ratings')
    rater = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings')
    rated_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ratings')
    score = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('ride', 'rater', 'rated_user')
