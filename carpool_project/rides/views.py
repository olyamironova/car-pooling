import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from django.db.models import Q, Count

from .models import UserProfile, Office, Ride, RidePassenger, RideRating
from .forms import (RegisterForm, UserProfileForm, RideCreateForm,
                    OfficeForm, JoinRideForm, RideFilterForm)
from .utils import (get_route_osrm, detect_city_from_coords,
                    geocode_address, interpolate_route,
                    haversine_distance, compare_distances)


def index(request):
    """Main page with map showing offices and active rides"""
    offices = Office.objects.filter(is_active=True)
    active_rides = Ride.objects.filter(
        status__in=['scheduled', 'active']
    ).select_related('driver', 'office').order_by('departure_time')[:10]

    offices_data = [
        {
            'id': o.id,
            'name': o.name,
            'address': o.address,
            'city': o.city,
            'lat': o.lat,
            'lon': o.lon,
            'description': o.description,
        }
        for o in offices
    ]

    rides_data = []
    for ride in active_rides:
        try:
            passengers_count = ride.passengers.filter(status='confirmed').count()
            rides_data.append({
                'id': ride.id,
                'driver': ride.driver.get_full_name() or ride.driver.username,
                'departure_address': ride.departure_address,
                'departure_lat': ride.departure_lat,
                'departure_lon': ride.departure_lon,
                'office_name': ride.office.name,
                'office_lat': ride.office.lat,
                'office_lon': ride.office.lon,
                'departure_time': ride.departure_time.strftime('%d.%m %H:%M'),
                'free_seats': ride.available_seats - passengers_count,
                'status': ride.status,
            })
        except Exception:
            pass

    context = {
        'offices': offices,
        'offices_json': json.dumps(offices_data),
        'rides_json': json.dumps(rides_data),
        'active_rides': active_rides,
    }
    return render(request, 'rides/index.html', context)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()

            role = form.cleaned_data.get('role', 'passenger')
            profile = UserProfile.objects.create(
                user=user,
                role=role,
                phone=form.cleaned_data.get('phone', ''),
                city=form.cleaned_data.get('city', ''),
                home_address=form.cleaned_data.get('home_address', ''),
                home_lat=form.cleaned_data.get('home_lat'),
                home_lon=form.cleaned_data.get('home_lon'),
                car_model=form.cleaned_data.get('car_model', ''),
                car_plate=form.cleaned_data.get('car_plate', ''),
                car_seats=form.cleaned_data.get('car_seats') or 3,
            )

            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.first_name or user.username}!')
            return redirect('index')
    else:
        form = RegisterForm()

    return render(request, 'rides/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', 'index')
            return redirect(next_url)
        else:
            messages.error(request, 'Неверный логин или пароль')

    return render(request, 'rides/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'role': 'passenger'}
    )

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save()
            request.user.first_name = form.cleaned_data.get('first_name', '')
            request.user.last_name = form.cleaned_data.get('last_name', '')
            request.user.email = form.cleaned_data.get('email', '')
            request.user.save()
            messages.success(request, 'Профиль обновлён!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)

    rides_as_driver = Ride.objects.filter(driver=request.user).order_by('-departure_time')[:5]
    rides_as_passenger = RidePassenger.objects.filter(
        passenger=request.user
    ).select_related('ride', 'ride__office', 'ride__driver').order_by('-joined_at')[:5]

    context = {
        'profile': profile,
        'form': form,
        'rides_as_driver': rides_as_driver,
        'rides_as_passenger': rides_as_passenger,
    }
    return render(request, 'rides/profile.html', context)


@login_required
def ride_list(request):
    form = RideFilterForm(request.GET)
    rides = Ride.objects.filter(
        status='scheduled'
    ).select_related('driver', 'driver__profile', 'office').order_by('departure_time')

    if form.is_valid():
        office = form.cleaned_data.get('office')
        city = form.cleaned_data.get('city')
        date = form.cleaned_data.get('date')

        if office:
            rides = rides.filter(office=office)
        if city:
            rides = rides.filter(departure_city__icontains=city)
        if date:
            rides = rides.filter(departure_time__date=date)

    rides_with_info = []
    for ride in rides:
        passengers_count = ride.passengers.filter(status='confirmed').count()
        can_join, reason = ride.can_join(request.user)
        rides_with_info.append({
            'ride': ride,
            'passengers_count': passengers_count,
            'free_seats': ride.available_seats - passengers_count,
            'can_join': can_join,
            'join_reason': reason,
        })

    context = {
        'rides': rides_with_info,
        'filter_form': form,
        'offices': Office.objects.filter(is_active=True),
    }
    return render(request, 'rides/ride_list.html', context)


@login_required
def ride_create(request):
    try:
        profile = request.user.profile
        if not profile.is_driver() and not profile.is_admin():
            messages.error(request, 'Только водители могут создавать поездки')
            return redirect('ride_list')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Заполните профиль')
        return redirect('profile')

    offices = Office.objects.filter(is_active=True)

    if request.method == 'POST':
        form = RideCreateForm(request.POST)
        if form.is_valid():
            ride = form.save(commit=False)
            ride.driver = request.user
            ride.total_seats = ride.available_seats

            # Get route from OSRM
            dep_lat = form.cleaned_data.get('departure_lat')
            dep_lon = form.cleaned_data.get('departure_lon')
            office = form.cleaned_data['office']

            if dep_lat and dep_lon:
                route = get_route_osrm(dep_lat, dep_lon, office.lat, office.lon)
                ride.route_distance_km = route['distance_km']
                ride.route_duration_min = route['duration_min']
                # Store interpolated coordinates for smooth simulation
                coords = interpolate_route(route['coords'], num_points=150)
                ride.route_geometry = json.dumps(coords)

                # Detect city
                if not form.cleaned_data.get('departure_city'):
                    ride.departure_city = detect_city_from_coords(dep_lat, dep_lon)
                else:
                    ride.departure_city = form.cleaned_data['departure_city']

                ride.current_lat = dep_lat
                ride.current_lon = dep_lon

            ride.save()
            messages.success(request, 'Поездка создана!')
            return redirect('ride_detail', pk=ride.pk)
    else:
        # Pre-fill from driver's home address
        initial = {}
        try:
            profile = request.user.profile
            if profile.home_address:
                initial['departure_address'] = profile.home_address
                initial['departure_lat'] = profile.home_lat
                initial['departure_lon'] = profile.home_lon
                initial['departure_city'] = profile.city
        except Exception:
            pass
        form = RideCreateForm(initial=initial)

    offices_data = [
        {'id': o.id, 'name': o.name, 'address': o.address,
         'lat': o.lat, 'lon': o.lon, 'city': o.city}
        for o in offices
    ]

    context = {
        'form': form,
        'offices': offices,
        'offices_json': json.dumps(offices_data),
    }
    return render(request, 'rides/ride_create.html', context)


@login_required
def ride_detail(request, pk):
    ride = get_object_or_404(
        Ride.objects.select_related('driver', 'driver__profile', 'office'),
        pk=pk
    )
    passengers = ride.passengers.filter(
        status='confirmed'
    ).select_related('passenger', 'passenger__profile')

    can_join, join_reason = ride.can_join(request.user)
    is_passenger = ride.passengers.filter(
        passenger=request.user, status='confirmed'
    ).exists()
    is_driver = ride.driver == request.user

    coords = []

    if ride.route_geometry:
        try:
            all_coords = json.loads(ride.route_geometry)
            coords = all_coords[::3]
        except (json.JSONDecodeError, TypeError):
            coords = []

    if not coords and ride.departure_lat and ride.departure_lon:
        try:
            route = get_route_osrm(
                ride.departure_lat, ride.departure_lon,
                ride.office.lat, ride.office.lon
            )
            coords = route.get('coords', [])

            if coords:
                interpolated = interpolate_route(coords, num_points=150)
                ride.route_geometry = json.dumps(interpolated)
                ride.route_distance_km = route.get('distance_km')
                ride.route_duration_min = route.get('duration_min')
                ride.save(update_fields=[
                    'route_geometry',
                    'route_distance_km',
                    'route_duration_min'
                ])
                coords = interpolated[::3]
        except Exception as e:
            print(f"[ride_detail] OSRM fallback error: {e}")
            coords = []

    if not coords and ride.departure_lat and ride.departure_lon:
        coords = [
            [float(ride.departure_lon), float(ride.departure_lat)],
            [float(ride.office.lon), float(ride.office.lat)],
        ]

    distance_comparison = None
    if ride.departure_lat and ride.departure_lon:
        try:
            distance_comparison = compare_distances(
                ride.departure_lat, ride.departure_lon,
                ride.office.lat, ride.office.lon
            )
        except Exception as e:
            print(f"[ride_detail] compare_distances error: {e}")

    context = {
        'ride': ride,
        'passengers': passengers,
        'can_join': can_join,
        'join_reason': join_reason,
        'is_passenger': is_passenger,
        'is_driver': is_driver,
        'join_form': JoinRideForm(),
        'coords_json': json.dumps(coords),
        'distance_comparison': distance_comparison,
    }
    return render(request, 'rides/ride_detail.html', context)


@login_required
@require_POST
def join_ride(request, pk):
    ride = get_object_or_404(Ride, pk=pk)
    can_join, reason = ride.can_join(request.user)

    if not can_join:
        messages.error(request, reason)
        return redirect('ride_detail', pk=pk)

    form = JoinRideForm(request.POST)
    pickup_lat = None
    pickup_lon = None
    pickup_address = ''

    if form.is_valid():
        pickup_address = form.cleaned_data.get('pickup_address', '')
        pickup_lat = form.cleaned_data.get('pickup_lat')
        pickup_lon = form.cleaned_data.get('pickup_lon')

    RidePassenger.objects.create(
        ride=ride,
        passenger=request.user,
        status='confirmed',
        pickup_address=pickup_address or ride.departure_address,
        pickup_lat=pickup_lat or ride.departure_lat,
        pickup_lon=pickup_lon or ride.departure_lon,
    )
    messages.success(request, 'Вы успешно присоединились к поездке!')
    return redirect('ride_detail', pk=pk)


@login_required
@require_POST
def leave_ride(request, pk):
    ride = get_object_or_404(Ride, pk=pk)
    passenger = get_object_or_404(RidePassenger, ride=ride, passenger=request.user)
    passenger.status = 'cancelled'
    passenger.save()
    messages.info(request, 'Вы покинули поездку')
    return redirect('ride_detail', pk=pk)


@login_required
@require_POST
def start_ride(request, pk):
    ride = get_object_or_404(Ride, pk=pk)
    if ride.driver != request.user:
        messages.error(request, 'Только водитель может начать поездку')
        return redirect('ride_detail', pk=pk)
    if ride.status != 'scheduled':
        messages.error(request, 'Поездка уже началась')
        return redirect('ride_detail', pk=pk)

    ride.status = 'active'
    ride.save()
    messages.success(request, 'Поездка начата!')
    return redirect('ride_simulation', pk=pk)


@login_required
def ride_simulation(request, pk):
    ride = get_object_or_404(
        Ride.objects.select_related('driver', 'office'),
        pk=pk
    )

    if ride.driver != request.user and not request.user.is_staff:
        is_passenger = ride.passengers.filter(passenger=request.user).exists()
        if not is_passenger:
            messages.error(request, 'У вас нет доступа к этой поездке')
            return redirect('ride_detail', pk=pk)

    coords = []
    if ride.route_geometry:
        try:
            coords = json.loads(ride.route_geometry)
        except Exception:
            pass

    context = {
        'ride': ride,
        'coords_json': json.dumps(coords),
        'is_driver': ride.driver == request.user,
    }
    return render(request, 'rides/ride_simulation.html', context)


@login_required
def cancel_ride(request, pk):
    ride = get_object_or_404(Ride, pk=pk)
    if ride.driver != request.user and not request.user.is_staff:
        messages.error(request, 'Нет прав')
        return redirect('ride_detail', pk=pk)

    ride.status = 'cancelled'
    ride.save()
    messages.info(request, 'Поездка отменена')
    return redirect('ride_list')


@login_required
def office_list(request):
    offices = Office.objects.all().annotate(
        rides_count=Count('rides')
    )
    return render(request, 'rides/office_list.html', {'offices': offices})


@login_required
def office_create(request):
    if not (request.user.is_staff or
            (hasattr(request.user, 'profile') and request.user.profile.is_admin())):
        messages.error(request, 'Только администраторы могут добавлять офисы')
        return redirect('office_list')

    if request.method == 'POST':
        form = OfficeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Офис добавлен!')
            return redirect('office_list')
    else:
        form = OfficeForm()

    return render(request, 'rides/office_form.html', {'form': form, 'action': 'Добавить'})


@login_required
def office_edit(request, pk):
    if not (request.user.is_staff or
            (hasattr(request.user, 'profile') and request.user.profile.is_admin())):
        messages.error(request, 'Только администраторы могут редактировать офисы')
        return redirect('office_list')

    office = get_object_or_404(Office, pk=pk)
    if request.method == 'POST':
        form = OfficeForm(request.POST, request.FILES, instance=office)
        if form.is_valid():
            form.save()
            messages.success(request, 'Офис обновлён!')
            return redirect('office_list')
    else:
        form = OfficeForm(instance=office)

    return render(request, 'rides/office_form.html', {
        'form': form, 'office': office, 'action': 'Редактировать'
    })


@login_required
def office_delete(request, pk):
    if not (request.user.is_staff or
            (hasattr(request.user, 'profile') and request.user.profile.is_admin())):
        messages.error(request, 'Нет прав')
        return redirect('office_list')

    office = get_object_or_404(Office, pk=pk)
    if request.method == 'POST':
        office.delete()
        messages.success(request, 'Офис удалён')
        return redirect('office_list')

    return render(request, 'rides/office_confirm_delete.html', {'office': office})


def api_geocode(request):
    address = request.GET.get('address', '')
    if not address:
        return JsonResponse({'error': 'No address'}, status=400)
    result = geocode_address(address)
    if result:
        return JsonResponse(result)
    return JsonResponse({'error': 'Not found'}, status=404)


def api_route(request):
    try:
        from_lat = float(request.GET.get('from_lat'))
        from_lon = float(request.GET.get('from_lon'))
        to_lat = float(request.GET.get('to_lat'))
        to_lon = float(request.GET.get('to_lon'))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid params'}, status=400)

    route = get_route_osrm(from_lat, from_lon, to_lat, to_lon)
    return JsonResponse(route)


def api_detect_city(request):
    try:
        lat = float(request.GET.get('lat'))
        lon = float(request.GET.get('lon'))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid params'}, status=400)

    city = detect_city_from_coords(lat, lon)
    return JsonResponse({'city': city})


def api_compare_distances(request):
    try:
        lat1 = float(request.GET.get('lat1'))
        lon1 = float(request.GET.get('lon1'))
        lat2 = float(request.GET.get('lat2'))
        lon2 = float(request.GET.get('lon2'))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid params'}, status=400)

    result = compare_distances(lat1, lon1, lat2, lon2)
    return JsonResponse(result)


def api_rides_map(request):
    rides = Ride.objects.filter(
        status__in=['scheduled', 'active']
    ).select_related('driver', 'office')

    data = []
    for ride in rides:
        pcount = ride.passengers.filter(status='confirmed').count()
        data.append({
            'id': ride.id,
            'departure_lat': ride.departure_lat,
            'departure_lon': ride.departure_lon,
            'departure_address': ride.departure_address,
            'office_lat': ride.office.lat,
            'office_lon': ride.office.lon,
            'office_name': ride.office.name,
            'driver': ride.driver.get_full_name() or ride.driver.username,
            'departure_time': ride.departure_time.strftime('%d.%m %H:%M'),
            'free_seats': ride.available_seats - pcount,
            'status': ride.status,
        })
    return JsonResponse({'rides': data})
