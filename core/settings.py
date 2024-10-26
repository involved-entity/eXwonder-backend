import os
from datetime import timedelta
from pathlib import Path

from environ import Env

BASE_DIR = Path(__file__).resolve().parent.parent

env = Env()
Env.read_env(os.path.join(BASE_DIR, ".env"))

HOST = env("HOST", default="http://localhost:8000/")
SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS").split(", ")

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework.authtoken',
    'dj_rest_auth',
    'drf_spectacular',
    'corsheaders',

    'users.apps.UsersConfig',
    'posts.apps.PostsConfig'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOWED_ORIGINS = (
    'http://localhost:5173',
    'http://localhost:8080'
)

CORS_ALLOW_METHODS = (
    'GET',
    'POST',
    'DELETE',
    'PUT',
    'PATCH'
)

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates/")],
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

WSGI_APPLICATION = 'core.wsgi.application'

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DATABASE_NAME"),
        "USER": env("DATABASE_USER"),
        "PASSWORD": env("DATABASE_PASSWORD"),
        "HOST": env("DATABASE_HOST"),
        "PORT": env("DATABASE_PORT"),
    }
}

LOGGING = {
    "version": 1,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler"
        }
    },
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": env("DJANGO_LOG_LEVEL", default="DEBUG")
        }
    },
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

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("DJANGO_CACHE_URL"),
        "TIMEOUT": 60*60*24,
    }
}

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

USER_RELATED_CACHE_NAME_SEP = ":"
USER_UPDATES_CACHE_NAME = "updates"
USER_POSTS_CACHE_NAME = "posts"
POSTS_LIKED_TOP_CACHE_NAME = "posts:liked"
POSTS_RECENT_TOP_CACHE_NAME = "posts:recent"

USER_UPDATES_CACHE_TIME = 60*10
POSTS_RECENT_TOP_CACHE_TIME = 60*60

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "users.authentication.TokenAuthentication",
        'rest_framework.authentication.SessionAuthentication'
    ],
    "PAGE_SIZE": 50,
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'eXwonder',
    'DESCRIPTION': '',
    'VERSION': '1.2.0',
}

REST_AUTH = {
    "OLD_PASSWORD_FIELD_ENABLED": True,
    "PASSWORD_RESET_SERIALIZER": "users.serializers.PasswordResetSerializer",
}

AUTH_USER_MODEL = "users.ExwonderUser"

DEFAULT_USER_TIMEZONE = "Europe/London"
DEFAULT_USER_AVATAR_PATH = "default-user-icon.jpg"

CUSTOM_USER_AVATARS_DIR = "avatars"
POSTS_IMAGES_DIR = "posts_images"
TEST_IMAGES_DIR = "test_images"

TOKEN_EXP_TIME = timedelta(days=30)
LAST_LOGIN_UPDATE_TIME = timedelta(hours=3)
TWO_FACTOR_AUTHENTICATION_CODE_LENGTH = 5
TWO_FACTOR_AUTHENTICATION_CODE_LIVETIME = 60 * 10   # seconds

CROPPED_IMAGE_POSTFIX = '_crop'

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = "noreply@exwonder"

CELERY_BROKER_URL = env("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND")

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = "static"
STATICFILES_DIRS = [
    BASE_DIR / "staticfiles/"
]
MEDIA_URL = "/media/"
MEDIA_ROOT = "mediafiles"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
