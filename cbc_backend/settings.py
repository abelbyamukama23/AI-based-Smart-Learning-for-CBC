"""
CBC Digital Learning Platform — Django Settings
Follows Stage E Architectural Design + Stage F DB Design conventions.
"""

from pathlib import Path
from datetime import timedelta
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Security ────────────────────────────────────────────────────────────────
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1").split(",")

# ─── Installed Apps ───────────────────────────────────────────────────────────
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "storages",
]

LOCAL_APPS = [
    "apps.accounts",
    "apps.curriculum",
    "apps.ai_tutor",
    "apps.feed",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ─── Middleware ───────────────────────────────────────────────────────────────
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",          # Must be first
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "cbc_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "cbc_backend.wsgi.application"

# ─── Database (SQLite for MVP; swap to PostgreSQL for production) ─────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ─── Custom Auth User Model ───────────────────────────────────────────────────
AUTH_USER_MODEL = "accounts.User"

# ─── Password Validation (NFR-SEC-03) ────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ─── Internationalisation ─────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Kampala"   # EAT = UTC+3 per Stage F design
USE_I18N = True
USE_TZ = True

# ─── Static Files ─────────────────────────────────────────────────────────────
STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── Django REST Framework ────────────────────────────────────────────────────
REST_FRAMEWORK = {
    # JWT as default authentication (NFR-SEC-03, NFR-SEC-04)
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    # All endpoints require authentication by default; override per-view where needed
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # Consistent JSON rendering
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    # Filtering support for curriculum browsing (FR-L-03)
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    # Pagination for feed and curriculum lists
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    # Exception handler (returns consistent error envelopes)
    "EXCEPTION_HANDLER": "cbc_backend.utils.custom_exception_handler",
}

# ─── SimpleJWT Configuration (Stage F: access 5min, refresh 7 days) ──────────
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),   # Extended for demo
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    # Include role in token for client-side routing
    "TOKEN_OBTAIN_SERIALIZER": "apps.accounts.serializers.CBCTokenObtainPairSerializer",
}

# ─── CORS (allow frontend dev server) ────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_CREDENTIALS = True

# ─── OpenAI (AI Tutor — FR-AI-01 to FR-AI-05) ────────────────────────────────
OPENAI_API_KEY = config("OPENAI_API_KEY", default="")

# ─── Cloudflare R2 File Storage (Library Agent) ───────────────────────────────
CLOUDFLARE_R2_ACCOUNT_ID      = config("CLOUDFLARE_R2_ACCOUNT_ID", default="")
CLOUDFLARE_R2_ACCESS_KEY_ID   = config("CLOUDFLARE_R2_ACCESS_KEY_ID", default="")
CLOUDFLARE_R2_SECRET_ACCESS_KEY = config("CLOUDFLARE_R2_SECRET_ACCESS_KEY", default="")
CLOUDFLARE_R2_BUCKET_NAME     = config("CLOUDFLARE_R2_BUCKET_NAME", default="")
CLOUDFLARE_R2_ENDPOINT_URL    = config("CLOUDFLARE_R2_ENDPOINT_URL", default="")
CLOUDFLARE_R2_PUBLIC_URL      = config("CLOUDFLARE_R2_PUBLIC_URL", default="")

# Use R2 for media files when credentials are configured, else fall back to local
if CLOUDFLARE_R2_ACCESS_KEY_ID and CLOUDFLARE_R2_BUCKET_NAME:
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    AWS_ACCESS_KEY_ID        = CLOUDFLARE_R2_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY    = CLOUDFLARE_R2_SECRET_ACCESS_KEY
    AWS_STORAGE_BUCKET_NAME  = CLOUDFLARE_R2_BUCKET_NAME
    AWS_S3_ENDPOINT_URL      = CLOUDFLARE_R2_ENDPOINT_URL
    AWS_S3_REGION_NAME       = "auto"
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    AWS_DEFAULT_ACL          = None        # R2 does not use ACLs
    AWS_S3_FILE_OVERWRITE    = False       # Preserve original filenames
    AWS_QUERYSTRING_AUTH     = False       # Clean public-style URLs
    MEDIA_URL = (CLOUDFLARE_R2_PUBLIC_URL.rstrip("/") + "/") if CLOUDFLARE_R2_PUBLIC_URL else "/media/"
else:
    MEDIA_ROOT = BASE_DIR / "media"
    MEDIA_URL  = "/media/"

# ─── ChromaDB Vector Store path (RAG / Library Agent) ────────────────────────
CHROMADB_PATH = str(BASE_DIR / ".chromadb")
