from pathlib import Path
import os
from dotenv import load_dotenv
import google.generativeai as genai   # import 1 lần thôi

# ==========================
# Base / Env
# ==========================
BASE_DIR = Path(__file__).resolve().parent.parent

# Load file .env
load_dotenv(BASE_DIR / ".env")

# ==========================
# Django Settings
# ==========================
SECRET_KEY = 'django-insecure-...'
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    # mặc định
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # channels
    "channels",

    # app humanize
    'django.contrib.humanize',

    # app của bạn
    'app',
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

ROOT_URLCONF = 'webchothuetro.urls'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
            ],
        },
    },
]

WSGI_APPLICATION = 'webchothuetro.wsgi.application'
ASGI_APPLICATION = "webchothuetro.asgi.application"

# ==========================
# Channels
# ==========================
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}

# ==========================
# Database
# ==========================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ==========================
# Auth
# ==========================
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/login/'

# ==========================
# I18N / L10N
# ==========================
LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True
USE_L10N = True

# ==========================
# Static / Media
# ==========================
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==========================
# CSRF
# ==========================
CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1:8000', 'http://localhost:8000']

# ==========================
# API Keys
# ==========================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-...")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBlwO47z_Fo6tAn6k5yHiX8gp8I0yQsceQ")


# ==========================
# Gemini Config
# ==========================
genai.configure(api_key=GEMINI_API_KEY)

def ask_gemini(prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")  # free model
    response = model.generate_content(prompt)
    return response.text
# ==========================
# Email config
# ==========================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "nguyenphuocnguyen7789@gmail.com"
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "vilqvnpznsfmskjt")  # lấy từ .env, fallback nếu .env trống

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
CONTACT_EMAIL = "admin@gmail.com"



