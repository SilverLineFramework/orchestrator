"""Django settings for arts_api project.

Generated by 'django-admin startproject' using Django 3.0.3.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
import json
import datetime

# --------------------------------------------------------------------------- #
#                                 Django Core                                 #
# --------------------------------------------------------------------------- #

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTS_DIR = os.path.dirname(BASE_DIR)


# --------------------------------- Security -------------------------------- #

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Load key file; forgives errors if running in debug mode.
try:
    with open(os.path.join(ARTS_DIR, "key.json")) as f:
        _key_file = json.load(f)
    SECRET_KEY = _key_file["key"]
except (FileNotFoundError, KeyError):
    if not DEBUG:
        raise Exception("Secret key file `key.json` not found.")
    else:
        SECRET_KEY = "NOT_A_SECRET_KEY"

# Includes 'localhost' if running in DEBUG=True.
# https://docs.djangoproject.com/en/4.0/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []


# ------------------------------ Server Sources ----------------------------- #

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'arts_core.apps.ArtsCoreConfig',
    'wasm_files'
]

# All default
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'arts_api.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(os.path.dirname(__file__), 'templates')],
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

WSGI_APPLICATION = 'arts_api.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': (
        'django.contrib.auth.password_validation.'
        'UserAttributeSimilarityValidator')},
    {'NAME':
        'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME':
        'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME':
        'django.contrib.auth.password_validation.NumericPasswordValidator'}
]


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Static root
STATIC_ROOT = "./public"

# Rest framework
REST_FRAMEWORK = {
    # When you enable API versioning, the request.version attribute will
    # contain a string that corresponds to the version requested in the
    # incoming client request.
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    # Permission settings
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],
    # Authentication settings
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
}

# JWT settings
JWT_AUTH = {
    'JWT_ENCODE_HANDLER':
        'rest_framework_jwt.utils.jwt_encode_handler',

    'JWT_DECODE_HANDLER':
        'rest_framework_jwt.utils.jwt_decode_handler',

    'JWT_PAYLOAD_HANDLER':
        'rest_framework_jwt.utils.jwt_payload_handler',

    'JWT_PAYLOAD_GET_USER_ID_HANDLER':
        'rest_framework_jwt.utils.jwt_get_user_id_from_payload_handler',

    'JWT_RESPONSE_PAYLOAD_HANDLER':
        'rest_framework_jwt.utils.jwt_response_payload_handler',

    'JWT_SECRET_KEY': SECRET_KEY,
    'JWT_GET_USER_SECRET_KEY': None,
    'JWT_PUBLIC_KEY': None,
    'JWT_PRIVATE_KEY': None,
    'JWT_ALGORITHM': 'HS256',
    'JWT_VERIFY': True,
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_LEEWAY': 0,
    'JWT_EXPIRATION_DELTA': datetime.timedelta(seconds=300),
    'JWT_AUDIENCE': None,
    'JWT_ISSUER': None,

    'JWT_ALLOW_REFRESH': False,
    'JWT_REFRESH_EXPIRATION_DELTA': datetime.timedelta(days=7),

    'JWT_AUTH_HEADER_PREFIX': 'Bearer',
    'JWT_AUTH_COOKIE': None,
}


# --------------------------------------------------------------------------- #
#                                     MQTT                                    #
# --------------------------------------------------------------------------- #

# MQTT Server
MQTT_FILE = os.path.join(ARTS_DIR, 'mqtt.json')
try:
    with open(MQTT_FILE) as f:
        _mqtt_file = json.load(f)
    REALM = _mqtt_file['realm']
    MQTT_ROOT = "{}/proc".format(REALM)
    MQTT_HOST = _mqtt_file['host']
    MQTT_PORT = _mqtt_file['port']
except (FileNotFoundError, KeyError):
    REALM = "realm"
    MQTT_ROOT = "realm/proc"
    MQTT_HOST = "localhost"
    MQTT_PORT = 1883

# MQTT Credentials
CREDENTIAL_FILE = os.path.join(ARTS_DIR, 'credentials.json')
try:
    with open(CREDENTIAL_FILE) as f:
        _mqtt_credentials = json.load(f)
    MQTT_USERNAME = _mqtt_credentials['username']
    MQTT_PASSWORD = _mqtt_credentials['password']
except (FileNotFoundError, KeyError):
    MQTT_USERNAME = "ARTS"
    MQTT_PASSWORD = ""

# Visualisation info for graph display
WEB_CLIENT_MQTT = {
    "wc_host"    : "arena-dev1.conix.io",
    "wc_ws_path" : "mqtt/"
}

# TODO: generate mqtt_password (aka mqtt_token) using self.jwt_config (JWT
# settings in settings.py)

# Error channel
MQTT_ERR = "{}/err".format(MQTT_ROOT)

MQTT_TOPICS = {
    '{}/{}'.format(MQTT_ROOT, endpoint): endpoint
    for endpoint in ['reg', 'control', 'debug', 'keepalive', 'profile'] 
}

# Directory to save data
DATA_DIR = os.path.join(ARTS_DIR, "data")

# Directory to save wasm files
WASM_DIR = "wasm_files/uploads"
