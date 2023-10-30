"""
Django settings for reporter project.

Generated by 'django-admin startproject' using Django 4.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

from pathlib import Path
import os
import logging
from django.core.management.utils import get_random_secret_key

logger = logging.getLogger(__name__)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', None)
if not SECRET_KEY:
    logger.warning("Missing DJANGO_SECRET_KEY environment variable. Generating random secret key.")
SECRET_KEY = get_random_secret_key()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', False)

TENANT = os.environ.get('TENANT', None)
if not TENANT:
    logger.warning("Missing TENANT environment variable")

INSTANCE = os.environ.get('INSTANCE', None)
if not TENANT:
    logger.warning("Missing INSTANCE environment variable")

METADATA_NAME = os.environ.get('METADATA_NAME', None)
if not METADATA_NAME:
    logger.warning("Missing METADATA_NAME environment variable")

# Token used for JupyterHub access
JUPYTERHUB_TOKEN = os.environ.get('JUPYTERHUB_TOKEN', None)
if not JUPYTERHUB_TOKEN:
    logger.warning("Missing JUPYTERHUB_TOKEN environment variable")

# Token used for GitHub API access
GITHUB_API_TOKEN = os.environ.get('GITHUB_API_TOKEN', None)
if not GITHUB_API_TOKEN:
    logger.warning("Missing GITHUB_API_TOKEN environment variable")

# Token used for Google Serp API
SERP_API_KEY = os.environ.get('SERP_API_KEY', None)
if not SERP_API_KEY:
    logger.warning("Missing SERP_API_KEY environment variable")

# API URL for JupyterHub
JUPYTERHUB_SERVER = os.environ.get('JUPYTERHUB_SERVER', None)
if not JUPYTERHUB_SERVER:
    logger.warning("Missing JUPYTERHUB_API environment variable")
    
# TAPIS API for Metadata
TAPIS_API_URL = os.environ.get('TAPIS_API_URL', None)
TAPIS_API = os.environ.get('TAPIS_API', None)
if not TAPIS_API or not TAPIS_API_URL:
    logger.warning("Missing TAPIS_API or TAPIS_API_URL environment variable")

TAPIS_SERVICE_TOKEN = os.environ.get('TAPIS_SERVICE_TOKEN', None)
if not TAPIS_SERVICE_TOKEN:
    logger.warning("Missing TAPIS_SERVICE_TOKEN environment variable")

# Tapis login client key and secret
TAPIS_CLIENT_ID = os.environ.get('TAPIS_CLIENT_ID', None)
TAPIS_CLIENT_KEY = os.environ.get('TAPIS_CLIENT_KEY', None)
if not TAPIS_CLIENT_ID or not TAPIS_CLIENT_KEY:
    logger.warning("Missing TAPIS_CLIENT_ID or TAPIS_CLIENT_KEY environment variable")


ALLOWED_HOSTS = ['*']

# Setup support for proxy headers
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

LOGIN_URL = '/auth/tapisauth'
LOGIN_REDIRECT_URL = ''

STATIC_URL = '/static/'
MEDIA_URL = '/media/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "reporter.apps.main",
    "reporter.apps.tapisauth",
    "reporter.apps.jupyterhub",
    "reporter.apps.tapis"
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

ROOT_URLCONF = "reporter.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'reporter/templates')],
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

WSGI_APPLICATION = "reporter.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTHENTICATION_BACKENDS = ['reporter.apps.tapisauth.backends.TapisOAuthBackend',
                           'django.contrib.auth.backends.ModelBackend']


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
