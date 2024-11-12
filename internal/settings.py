from pathlib import Path
from datetime import timedelta
import os
from storages.backends.s3boto3 import S3Boto3Storage
from firebase_admin import initialize_app, credentials
from google.auth import load_credentials_from_file
import os
from dotenv import load_dotenv 

load_dotenv() 


# DJANGO SETUP
BASE_DIR = Path(__file__).resolve().parent
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
DEBUG = True
ALLOWED_HOSTS = ["*"]
APPEND_SLASH=True 

TIME_ZONE = 'Asia/Bangkok'  # Set this to your desired timezone
USE_TZ = True


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'djoser',
    'fcm_django',
    'storages',

    'debug_toolbar',
    'teacher',
    'student',
    'school',
    'core'
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'internal.urls'

# Template Integration
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR.parent, 'templates'),  # Add this line to set your template root
        ],
        'APP_DIRS': True,
                'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    }
]
WSGI_APPLICATION = 'internal.wsgi.application'


# Database
DATABASES = {
    'default': {
       'ENGINE': 'django.db.backends.postgresql',
       'NAME': 'postgres',
       'USER': 'postgres',
       'PASSWORD': 'Pluem9988!',
       'HOST': 'localhost',
       'PORT': '5432',
    }
}


# DATABASES = {
#     'default': {
#        'ENGINE': 'django.db.backends.postgresql_psycopg2',
#        'NAME': 'railway',
#        'HOST': 'monorail.proxy.rlwy.net',
#        'USER': 'postgres',
#        'PASSWORD': 'AyDEBNsgiiBOdoNURGIMeqnIEzaNAVdm',
#        'PORT': '15052',
#     }
# }


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


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ]
}

# DJOSER

DJOSER = {
    "LOGIN_FIELD": "email",
    'PASSWORD_RESET_CONFIRM_URL': 'auth/password/reset/confirm/{uid}/{token}/',   
    # 'ACTIVATION_URL': 'auth/users/activate_request/{uid}/{token}',
    'SERIALIZERS' : {
        'user_create': 'core.serializers.UserCreateSerializer',
        "user": "djoser.serializers.UserSerializer",
        "current_user": 'core.serializers.UserSerializer',
        "user_delete": "djoser.serializers.UserSerializer",    
        },
    'EMAIL': {
        'password_reset': 'core.email.PasswordResetEmailTemplate'
    },
    # 'SEND_ACTIVATION_EMAIL': True,
    # 'SEND_CONFIRMATION_EMAIL':True,
}

SEND_ACTIVATION_EMAIL = True

SIMPLE_JWT = {
    'AUTH_HEADER_TYPES': ('JWT',),
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=10),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=365*100),
}

AUTH_USER_MODEL = 'core.User'

# Email Integration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL")


DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: True,
}



# STORAGE 
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")

AWS_S3_REGION_NAME = 'ap-southeast-2'  # e.g., us-east-1
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_S3_FILE_OVERWRITE = True

STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'

STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

class MediaStorage(S3Boto3Storage):
    location = 'media'
    file_overwrite = False

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_LOCATION = 'static'


# Notification System ( Firebase )
class CustomFirebaseCredentials(credentials.ApplicationDefault):
    def __init__(self, account_file_path: str):
        super().__init__()
        self._account_file_path = account_file_path

    def _load_credential(self):
        if not self._g_credential:
            self._g_credential, self._project_id = load_credentials_from_file(self._account_file_path,
                                                                              scopes=credentials._scopes)

custom_credentials = CustomFirebaseCredentials(os.getenv("FIREBASE_JSON_PATH"))
FIREBASE_MESSAGING_APP = initialize_app(custom_credentials, name='messaging')

FCM_DJANGO_SETTINGS = {
    "DEFAULT_FIREBASE_APP": FIREBASE_MESSAGING_APP,
     # default: _('FCM Django')
    "APP_VERBOSE_NAME": "Timeable",
    "ONE_DEVICE_PER_USER": False,
    "DELETE_INACTIVE_DEVICES": False,
}

# CELERY_TIMEZONE = "Asia/Thailand"
# CELERY_TASK_TRACK_STARTED = True
# CELERY_TASK_TIME_LIMIT = 30 * 60
# CELERY_BROKER_URL = 'redis://127.0.0.1:6379'
# CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379'
# CELERY_ACCEPT_CONTENT = ['application/json']
# CELERY_RESULT_SERIALIZER = 'json'
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_STORE_ERRORS_EVEN_IF_IGNORED = True
