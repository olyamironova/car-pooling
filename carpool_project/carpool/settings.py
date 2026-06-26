import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-carpool-secret-key-change-in-production-2024'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'rides',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'carpool.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'carpool.wsgi.application'
ASGI_APPLICATION = 'carpool.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'

STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# OSRM public server for routing
OSRM_SERVER = 'https://router.project-osrm.org'

# Nominatim for geocoding
NOMINATIM_USER_AGENT = 'carpool_app_2024'

CITY_BOUNDARIES = {
    'moscow': {
        'name': 'Москва',
        'lat_min': 55.48, 'lat_max': 56.02,
        'lon_min': 36.80, 'lon_max': 37.97,
        'center_lat': 55.7558,
        'center_lon': 37.6173,
    },
    'saint_petersburg': {
        'name': 'Санкт-Петербург',
        'lat_min': 59.74, 'lat_max': 60.15,
        'lon_min': 29.42, 'lon_max': 30.75,
        'center_lat': 59.9311,
        'center_lon': 30.3609,
    },
    'novosibirsk': {
        'name': 'Новосибирск',
        'lat_min': 54.74, 'lat_max': 55.18,
        'lon_min': 82.72, 'lon_max': 83.20,
        'center_lat': 54.9885,
        'center_lon': 82.9207,
    },
    'yekaterinburg': {
        'name': 'Екатеринбург',
        'lat_min': 56.66, 'lat_max': 56.96,
        'lon_min': 60.43, 'lon_max': 60.83,
        'center_lat': 56.8389,
        'center_lon': 60.6057,
    },
}
