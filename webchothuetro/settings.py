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



DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'


CSRF_TRUSTED_ORIGINS = os.getenv(
    "CSRF_TRUSTED_ORIGINS",
    "https://webchothuetro-production.up.railway.app"
).split(",")
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = [x.strip() for x in CSRF_TRUSTED_ORIGINS if x.strip()]

import os

# Lấy thông tin từ Biến Môi Trường trên Railway
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')

# Cấu hình chính thức
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': CLOUDINARY_CLOUD_NAME,
    'API_KEY': CLOUDINARY_API_KEY,
    'API_SECRET': CLOUDINARY_API_SECRET
}

# Đặt Cloudinary làm nơi lưu trữ mặc định cho TỆP MEDIA (ảnh tải lên)
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

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
    "cloudinary",
    "cloudinary_storage",

    # app humanize
    'django.contrib.humanize',

    # app của bạn
    'app',
]



MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', 
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
# -------------------------
# Env / Secret
# -------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-fallback-for-dev-only")
DEBUG = os.getenv("DEBUG", "True").lower() in ("1", "true", "yes")

# ALLOWED_HOSTS from env (comma separated)
allowed = os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
ALLOWED_HOSTS = [h.strip() for h in allowed if h.strip()]

# -------------------------
# Database via DATABASE_URL
# -------------------------
import dj_database_url

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    # If you're deploying to Railway/Heroku, enable ssl_require=True in production
    DATABASES = {
        "default": dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=not DEBUG)
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("PG_NAME", "webchothuetro"),
            "USER": os.getenv("PG_USER", "postgres"),
            "PASSWORD": os.getenv("PG_PASSWORD", "0123456"),
            "HOST": os.getenv("PG_HOST", "localhost"),
            "PORT": os.getenv("PG_PORT", "5432"),
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
USE_TZ = False
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



STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
