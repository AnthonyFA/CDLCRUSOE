"""
Base settings for a CRUSOE PAO wrapper (generic).

Environment parameterization:
  - PAO_ELEMENT:   wrapper slug (firewall, dnsfw, userBlock, mailFilter, rtbh, custom)
  - SECRET_KEY:    secret key
  - DEBUG:         '1' / '0'
  - ALLOWED_HOSTS: comma-separated list (e.g., "127.0.0.1,localhost")
  - TIME_ZONE:     time zone (default 'UTC')
  - STATIC_ROOT:   absolute path used to collect static files
  - DATABASE_URL:  optional (e.g., postgres://..., mysql://..., sqlite:///...)
  - CSRF_TRUSTED_ORIGINS: comma-separated list (e.g., https://host1,https://host2)
  - PAO_BACKEND_URL / PAO_API_KEY: device/service-specific parameters
"""

import os
from pathlib import Path

# --- Paths --------------------------------------------------------------------
BASE_DIR: Path = Path(__file__).resolve().parent.parent

# --- PAO parametrization ------------------------------------------------------
PAO_ELEMENT: str = os.getenv("PAO_ELEMENT", "firewall")
PAO_SLUG: str = PAO_ELEMENT  # alias 
PROJECT_NAME: str = f"{PAO_ELEMENT}_wrapper"
APP_NAME: str = f"{PAO_ELEMENT}_wrapper_project"

ROOT_URLCONF: str = os.getenv("APP_URLCONF_MODULE", f"{PROJECT_NAME}.urls")
WSGI_APPLICATION: str = os.getenv("WSGI_APP", f"{PROJECT_NAME}.wsgi.application")

# Optional: expose the app urlconf path so urls.py can pick it up via settings.APP_URLCONF
APP_URLCONF: str = os.getenv("APP_URLCONF", f"{APP_NAME}.urls")

# --- Security / Debug ---------------------------------------------------------
SECRET_KEY: str = os.getenv("SECRET_KEY", "!!!-INSECURE-DEFAULT-CHANGE-ME-!!!")
DEBUG: bool = os.getenv("DEBUG", "0") == "1"

ALLOWED_HOSTS = [
    h.strip() for h in os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if h.strip()
]
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# --- Apps ---------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    APP_NAME,  # your app wrapper (e.g., firewall_wrapper_project)
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [str(BASE_DIR / "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- Database -----------------------------------------------------------------
# Prefer DATABASE_URL; fallback to local SQLite.
DATABASES = {}
_db_default = f"sqlite:///{BASE_DIR / 'db.sqlite3'}"

DATABASE_URL = os.getenv("DATABASE_URL", _db_default)
if DATABASE_URL.startswith("sqlite:///"):
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATABASE_URL.replace("sqlite:///", ""),
    }
else:
    try:
        import dj_database_url  # pip install dj-database-url
        DATABASES["default"] = dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    except Exception:
        # Conservative fallback if dj_database_url is not available
        DATABASES["default"] = {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(BASE_DIR / "db.sqlite3"),
        }

# --- Password validators ------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- i18n ---------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("TIME_ZONE", "UTC")
USE_I18N = True
USE_L10N = True
USE_TZ = True

# --- Static files -------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = os.getenv("STATIC_ROOT", str(BASE_DIR / "static"))

# --- Django >= 3.2 default auto field ----------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# --- PAO integration parameters (example) -------------------------------------
# Useful for wrapper views (e.g., calls to the real device/API)
PAO_BACKEND_URL: str = os.getenv("PAO_BACKEND_URL", "")  # real device/API base URL
PAO_API_KEY: str = os.getenv("PAO_API_KEY", "")          # API key/token if applicable

# Optional hard cap if the tool doesn't expose capacity
PAO_MAX_CAPACITY: int = int(os.getenv("PAO_MAX_CAPACITY", "0"))
