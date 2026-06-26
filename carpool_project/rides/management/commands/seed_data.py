from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random


class Command(BaseCommand):
    help = 'Seed the database with demo data'

    def handle(self, *args, **options):
        from rides.models import UserProfile, Office, Ride, RidePassenger

        self.stdout.write('🌱 Seeding database...')

        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'Алексей',
                'last_name': 'Иванов',
                'email': 'admin@company.ru',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            UserProfile.objects.get_or_create(
                user=admin,
                defaults={'role': 'admin', 'city': 'Москва', 'phone': '+7 999 001-00-01'}
            )
            self.stdout.write(f'  ✅ Created admin: admin / admin123')

        offices_data = [
            {
                'name': 'Головной офис',
                'address': 'ул. Тверская, 1, Москва',
                'city': 'Москва',
                'lat': 55.7645,
                'lon': 37.6061,
                'description': 'Главный офис компании в центре Москвы',
            },
            {
                'name': 'Технопарк Сколково',
                'address': 'Нобелевская улица, 1, Москва',
                'city': 'Москва',
                'lat': 55.6960,
                'lon': 37.3567,
                'description': 'Инновационный центр, разработка',
            },
            {
                'name': 'СПб офис на Невском',
                'address': 'Невский проспект, 28, Санкт-Петербург',
                'city': 'Санкт-Петербург',
                'lat': 59.9348,
                'lon': 30.3246,
                'description': 'Офис в историческом центре Петербурга',
            },
            {
                'name': 'Новосибирский технохаб',
                'address': 'пр. Карла Маркса, 20, Новосибирск',
                'city': 'Новосибирск',
                'lat': 54.9896,
                'lon': 82.9035,
                'description': 'Офис в Академгородке',
            },
        ]

        offices = []
        for od in offices_data:
            office, created = Office.objects.get_or_create(
                name=od['name'],
                defaults={
                    'address': od['address'],
                    'city': od['city'],
                    'lat': od['lat'],
                    'lon': od['lon'],
                    'description': od['description'],
                }
            )
            offices.append(office)
            if created:
                self.stdout.write(f'  ✅ Created office: {office.name}')

        drivers_data = [
            {
                'username': 'driver1',
                'first_name': 'Михаил',
                'last_name': 'Петров',
                'city': 'Москва',
                'home_address': 'ул. Арбат, 25, Москва',
                'home_lat': 55.7486,
                'home_lon': 37.5958,
                'car_model': 'Toyota Camry',
                'car_plate': 'А123ВС77',
                'car_seats': 3,
            },
            {
                'username': 'driver2',
                'first_name': 'Елена',
                'last_name': 'Смирнова',
                'city': 'Москва',
                'home_address': 'Ленинградский проспект, 80, Москва',
                'home_lat': 55.7972,
                'home_lon': 37.5303,
                'car_model': 'Hyundai Sonata',
                'car_plate': 'В456ДЕ77',
                'car_seats': 4,
            },
            {
                'username': 'driver3',
                'first_name': 'Дмитрий',
                'last_name': 'Козлов',
                'city': 'Санкт-Петербург',
                'home_address': 'Лиговский проспект, 10, Санкт-Петербург',
                'home_lat': 59.9238,
                'home_lon': 30.3609,
                'car_model': 'Kia K5',
                'car_plate': 'Г789ЖЗ78',
                'car_seats': 3,
            },
        ]

        driver_users = []
        for dd in drivers_data:
            user, created = User.objects.get_or_create(
                username=dd['username'],
                defaults={
                    'first_name': dd['first_name'],
                    'last_name': dd['last_name'],
                    'email': f"{dd['username']}@company.ru",
                }
            )
            if created:
                user.set_password('pass123')
                user.save()
                UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'role': 'driver',
                        'city': dd['city'],
                        'home_address': dd['home_address'],
                        'home_lat': dd['home_lat'],
                        'home_lon': dd['home_lon'],
                        'car_model': dd['car_model'],
                        'car_plate': dd['car_plate'],
                        'car_seats': dd['car_seats'],
                        'phone': f'+7 999 {random.randint(100,999)}-{random.randint(10,99)}-{random.randint(10,99)}',
                        'rating': round(random.uniform(4.2, 5.0), 1),
                    }
                )
                self.stdout.write(f'  ✅ Created driver: {dd["username"]} / pass123')
            driver_users.append(user)

        passengers_data = [
            {'username': 'passenger1', 'first_name': 'Анна', 'last_name': 'Новикова', 'city': 'Москва', 'lat': 55.7559, 'lon': 37.5200},
            {'username': 'passenger2', 'first_name': 'Сергей', 'last_name': 'Морозов', 'city': 'Москва', 'lat': 55.7800, 'lon': 37.6500},
            {'username': 'passenger3', 'first_name': 'Мария', 'last_name': 'Волкова', 'city': 'Санкт-Петербург', 'lat': 59.9500, 'lon': 30.3200},
            {'username': 'passenger4', 'first_name': 'Игорь', 'last_name': 'Соколов', 'city': 'Новосибирск', 'lat': 54.9850, 'lon': 82.9100},
        ]

        passenger_users = []
        for pd in passengers_data:
            user, created = User.objects.get_or_create(
                username=pd['username'],
                defaults={
                    'first_name': pd['first_name'],
                    'last_name': pd['last_name'],
                    'email': f"{pd['username']}@company.ru",
                }
            )
            if created:
                user.set_password('pass123')
                user.save()
                UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'role': 'passenger',
                        'city': pd['city'],
                        'home_lat': pd['lat'],
                        'home_lon': pd['lon'],
                    }
                )
                self.stdout.write(f'  ✅ Created passenger: {pd["username"]} / pass123')
            passenger_users.append(user)

        now = timezone.now()
        rides_data = [
            {
                'driver': driver_users[0],
                'office': offices[0],
                'departure_address': 'ул. Арбат, 25, Москва',
                'departure_lat': 55.7486,
                'departure_lon': 37.5958,
                'departure_city': 'Москва',
                'departure_time': now + timedelta(hours=2),
                'available_seats': 3,
                'comment': 'Заберу с Арбата, место в машине ещё есть!',
                'route_distance_km': 5.2,
                'route_duration_min': 18.5,
            },
            {
                'driver': driver_users[1],
                'office': offices[1],
                'departure_address': 'Ленинградский пр., 80, Москва',
                'departure_lat': 55.7972,
                'departure_lon': 37.5303,
                'departure_city': 'Москва',
                'departure_time': now + timedelta(hours=1, minutes=30),
                'available_seats': 4,
                'comment': 'Еду в Сколково, место для 4 человек',
                'route_distance_km': 22.1,
                'route_duration_min': 42.0,
            },
            {
                'driver': driver_users[2],
                'office': offices[2],
                'departure_address': 'Лиговский пр., 10, СПб',
                'departure_lat': 59.9238,
                'departure_lon': 30.3609,
                'departure_city': 'Санкт-Петербург',
                'departure_time': now + timedelta(hours=3),
                'available_seats': 3,
                'comment': 'Из Лиговки до Невского',
                'route_distance_km': 3.8,
                'route_duration_min': 15.0,
            },
        ]

        for rd in rides_data:
            if not Ride.objects.filter(
                driver=rd['driver'],
                office=rd['office'],
                status='scheduled'
            ).exists():
                ride = Ride.objects.create(
                    driver=rd['driver'],
                    office=rd['office'],
                    departure_address=rd['departure_address'],
                    departure_lat=rd['departure_lat'],
                    departure_lon=rd['departure_lon'],
                    departure_city=rd['departure_city'],
                    departure_time=rd['departure_time'],
                    available_seats=rd['available_seats'],
                    total_seats=rd['available_seats'],
                    comment=rd.get('comment', ''),
                    route_distance_km=rd.get('route_distance_km'),
                    route_duration_min=rd.get('route_duration_min'),
                    current_lat=rd['departure_lat'],
                    current_lon=rd['departure_lon'],
                )
                self.stdout.write(f'  ✅ Created ride: {ride}')

                if rd['driver'] == driver_users[0] and passenger_users:
                    RidePassenger.objects.get_or_create(
                        ride=ride,
                        passenger=passenger_users[0],
                        defaults={
                            'status': 'confirmed',
                            'pickup_address': 'ул. Пречистенка, 10, Москва',
                            'pickup_lat': 55.7420,
                            'pickup_lon': 37.5960,
                        }
                    )

        self.stdout.write(self.style.SUCCESS('\n✨ Database seeded successfully!'))
        self.stdout.write('\n📋 Test accounts:')
        self.stdout.write('  Admin:      admin / admin123 (is_staff=True)')
        self.stdout.write('  Drivers:    driver1, driver2, driver3 / pass123')
        self.stdout.write('  Passengers: passenger1, passenger2, passenger3, passenger4 / pass123')
        self.stdout.write('\n🌆 Cities:')
        self.stdout.write('  Москва: driver1, driver2, passenger1, passenger2')
        self.stdout.write('  Санкт-Петербург: driver3, passenger3')
        self.stdout.write('  Новосибирск: passenger4')
