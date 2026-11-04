
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

def _load_env_file(filepath):
    if not filepath.exists():
        return False
    try:
        from dotenv import load_dotenv
        load_dotenv(filepath)
        return True
    except (ImportError, ModuleNotFoundError):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    k, v = line.split('=', 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k and k not in os.environ:
                        os.environ[k] = v
            return True
        except Exception:
            return False

if not _load_env_file(BASE_DIR / '.env'):
    _load_env_file(BASE_DIR / 'env')

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-6yd6j8)f&_2nj15kxq)799sf@x&cd$ai-+1dnsiq++p)*qbo0+')

DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't', 'yes')

ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', '*').split(',') if h.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'accounts.apps.AccountsConfig',
    'parking.apps.ParkingConfig',
    'bookings.apps.BookingsConfig',
    'payments.apps.PaymentsConfig',
    'lot_owner_panel.apps.LotOwnerPanelConfig',
    'admin_panel.apps.AdminPanelConfig',
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

ROOT_URLCONF = 'parkease.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'parking.context_processors.google_maps',
            ],
        },
    },
]

WSGI_APPLICATION = 'parkease.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'


MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 't', 'yes')
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False').lower() in ('true', '1', 't', 'yes')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'ParkEase <noreply@parkease.com>')
SERVER_EMAIL = os.getenv('SERVER_EMAIL', EMAIL_HOST_USER or 'noreply@parkease.com')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'bharvadiyasavan96@gmail.com')
OWNER_DEFAULT_EMAIL = os.getenv('OWNER_DEFAULT_EMAIL', 'savaniiictiu62@gmail.com')
USER_DEFAULT_EMAIL = os.getenv('USER_DEFAULT_EMAIL', 'saavanbaems@gmail.com')

_rzp_env_key = os.getenv('RAZORPAY_KEY_ID', '')
if not _rzp_env_key or _rzp_env_key in ('rzp_test_placeholder', 'TEST10000001'):
    _rzp_env_key = 'rzp_test_TvL77K63xBPjkg'
RAZORPAY_KEY_ID = _rzp_env_key
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', '1DP5mmOlF5G5agSecret')


GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')
GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY', '')
GOOGLE_ROUTES_API_KEY = os.getenv('GOOGLE_ROUTES_API_KEY', '')
