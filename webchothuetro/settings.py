# settings.py — cleaned & fixed (replace the top/middle parts accordingly)

from pathlib import Path
import os
from dotenv import load_dotenv
# optional: google generative ai (only if you actually use it elsewhere)
try:
    import google.generativeai as genai
except Exception:
    genai = None

# ==========================
# Base / Env
# ==========================
BASE_DIR = Path(__file__).resolve().parent.parent

# Load file .env (if exists)
load_dotenv(BASE_DIR / ".env")

# Secret + Debug
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-fallback-for-dev-only")
DEBUG = os.getenv("DEBUG", "True").lower() in ("1", "true", "yes")

# --------------------------
# Hosts & CSRF / Cookies
# --------------------------
# Default safe hosts (add your production host(s) here or via ENV ALLOWED_HOSTS)
default_allowed = os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost,webchothuetro-production.up.railway.app")
ALLOWED_HOSTS = [h.strip() for h in default_allowed.split(",") if h.strip()]

# CSRF trusted origins logic: local (http) vs production (https)
if DEBUG:
    CSRF_TRUSTED_ORIGINS = ["http://127.0.0.1:8000", "http://localhost:8000"]
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False
else:
    # If you have multiple production domains, set as comma separated in env var CSRF_TRUSTED_ORIGINS
    env_csrf = os.getenv("CSRF_TRUSTED_ORIGINS")
    if env_csrf:
        CSRF_TRUSTED_ORIGINS = [x.strip() for x in env_csrf.split(",") if x.strip()]
    else:
        CSRF_TRUSTED_ORIGINS = ["https://webchothuetro-production.up.railway.app"]
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True

# ==========================
# Cloudinary (media storage)
# ==========================
CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME") or os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY") or os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET") or os.getenv("CLOUDINARY_API_SECRET")

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": CLOUDINARY_CLOUD_NAME,
    "API_KEY": CLOUDINARY_API_KEY,
    "API_SECRET": CLOUDINARY_API_SECRET,
}

# If cloudinary credentials are present, use Cloudinary for media files.
# Otherwise fallback to local MEDIA (useful for dev).
if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
    DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
else:
    DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

# ==========================
# Installed apps & middleware
# ==========================
INSTALLED_APPS = [
    # django defaults
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # channels & cloudinary (only needed if installed)
    "channels",
    "cloudinary" if CLOUDINARY_CLOUD_NAME else None,
    "cloudinary_storage" if CLOUDINARY_CLOUD_NAME else None,

    # humanize & your app
    "django.contrib.humanize",
    "app",
]

# remove None entries if cloudinary not configured
INSTALLED_APPS = [a for a in INSTALLED_APPS if a]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "webchothuetro.urls"

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

WSGI_APPLICATION = "webchothuetro.wsgi.application"
ASGI_APPLICATION = "webchothuetro.asgi.application"

# ==========================
# Channels (local default)
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
# Database config
# ==========================
import dj_database_url

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
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
# Auth / i18n
# ==========================
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
LOGIN_URL = "/login/"

LANGUAGE_CODE = "vi"
TIME_ZONE = "Asia/Ho_Chi_Minh"
USE_I18N = True
USE_TZ = False
USE_L10N = True

# ==========================
# Static & Media
# ==========================
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# If using whitenoise for static files
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ==========================
# API keys + Gemini optional
# ==========================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-...")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if genai and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception:
        pass

def ask_gemini(prompt):
    if genai is None:
        raise RuntimeError("google.generativeai not installed")
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text

# ==========================
# Email config (keep or change)
# ==========================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "nguyenphuocnguyen7789@gmail.com")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
CONTACT_EMAIL = "admin@gmail.com"
