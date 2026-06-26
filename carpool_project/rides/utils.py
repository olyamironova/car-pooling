import math
import json
import requests
from django.conf import settings


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def manhattan_distance(lat1, lon1, lat2, lon2):
    """Approximate Manhattan distance (city blocks) in km"""
    lat_km = haversine_distance(lat1, lon1, lat1, lon2)
    lon_km = haversine_distance(lat1, lon1, lat2, lon1)
    return lat_km + lon_km


def get_route_osrm(from_lat, from_lon, to_lat, to_lon):
    """Get route from OSRM (Open Source Routing Machine)"""
    try:
        url = f"{settings.OSRM_SERVER}/route/v1/driving/{from_lon},{from_lat};{to_lon},{to_lat}"
        params = {
            'overview': 'full',
            'geometries': 'geojson',
            'steps': 'false',
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get('code') == 'Ok' and data.get('routes'):
            route = data['routes'][0]
            distance_km = route['distance'] / 1000
            duration_min = route['duration'] / 60
            coords = route['geometry']['coordinates']  # [[lon, lat], ...]
            return {
                'distance_km': round(distance_km, 2),
                'duration_min': round(duration_min, 1),
                'coords': coords,
                'method': 'osrm',
            }
    except Exception as e:
        pass

    distance = haversine_distance(from_lat, from_lon, to_lat, to_lon)
    # Estimate duration: average city speed ~30 km/h
    duration = (distance / 30) * 60
    coords = [[from_lon, from_lat], [to_lon, to_lat]]
    return {
        'distance_km': round(distance, 2),
        'duration_min': round(duration, 1),
        'coords': coords,
        'method': 'haversine',
    }


def detect_city_from_coords(lat, lon):
    from django.conf import settings
    cities = settings.CITY_BOUNDARIES

    for city_key, city_data in cities.items():
        if (city_data['lat_min'] <= lat <= city_data['lat_max'] and
                city_data['lon_min'] <= lon <= city_data['lon_max']):
            return city_data['name']

    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            'lat': lat,
            'lon': lon,
            'format': 'json',
            'accept-language': 'ru',
        }
        headers = {'User-Agent': settings.NOMINATIM_USER_AGENT}
        response = requests.get(url, params=params, headers=headers, timeout=5)
        data = response.json()
        address = data.get('address', {})
        city = (address.get('city') or address.get('town') or
                address.get('village') or address.get('state', ''))
        return city
    except Exception:
        return ''


def geocode_address(address):
    """Geocode address using Nominatim"""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': address,
            'format': 'json',
            'limit': 1,
            'accept-language': 'ru',
        }
        headers = {'User-Agent': settings.NOMINATIM_USER_AGENT}
        response = requests.get(url, params=params, headers=headers, timeout=5)
        results = response.json()
        if results:
            result = results[0]
            return {
                'lat': float(result['lat']),
                'lon': float(result['lon']),
                'display_name': result.get('display_name', address),
            }
    except Exception:
        pass
    return None


def interpolate_route(coords, num_points=100):
    """Interpolate route coordinates to have exactly num_points points"""
    if len(coords) <= 1:
        return coords
    if len(coords) >= num_points:
        step = len(coords) / num_points
        return [coords[int(i * step)] for i in range(num_points)]

    result = []
    segment_count = len(coords) - 1
    points_per_segment = max(1, num_points // segment_count)

    for i in range(segment_count):
        start = coords[i]
        end = coords[i + 1]
        for j in range(points_per_segment):
            t = j / points_per_segment
            lon = start[0] + t * (end[0] - start[0])
            lat = start[1] + t * (end[1] - start[1])
            result.append([lon, lat])

    result.append(coords[-1])
    return result


def compare_distances(lat1, lon1, lat2, lon2):
    """Compare different distance calculation methods"""
    haversine = haversine_distance(lat1, lon1, lat2, lon2)
    manhattan = manhattan_distance(lat1, lon1, lat2, lon2)

    try:
        osrm = get_route_osrm(lat1, lon1, lat2, lon2)
        osrm_dist = osrm['distance_km']
    except:
        osrm_dist = None

    return {
        'haversine_km': round(haversine, 2),
        'manhattan_km': round(manhattan, 2),
        'osrm_km': osrm_dist,
        'road_factor': round(osrm_dist / haversine, 2) if osrm_dist else None,
    }
