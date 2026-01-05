# ==========================================
# sofemci/settings.py - Configuration Django
# VERSION CORRIGÉE
# ==========================================

import os
import sys
from pathlib import Path
from decouple import config

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# ==========================================
# SECURITY CONFIGURATION
# ==========================================
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')
DEBUG = config('DEBUG', cast=bool, default=True)
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    cast=lambda v: [s.strip() for s in v.split(',')],
    default='127.0.0.1,localhost,0.0.0.0'
)

# ==========================================
# APPLICATION DEFINITION
# ==========================================
INSTALLED_APPS = [
    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',  
    'sofemci',
    
]

# Custom User Model
AUTH_USER_MODEL = 'sofemci.CustomUser'

MIDDLEWARE = [
    
    
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',  # Important pour l'admin
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'urls'

# ==========================================
# TEMPLATES CONFIGURATION
# ==========================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',  # Dossier templates principal
            BASE_DIR / 'sofemci' / 'templates',  # Templates spécifiques à l'app
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Custom context processors (si existent)
                # 'sofemci.context_processors.sofemci_config',
            ],
            # Retirez 'libraries' si custom_filters n'existe pas
            # 'libraries': {
            #     'custom_filters': 'sofemci.templatetags.custom_filters',
            # },
        },
    },
]

WSGI_APPLICATION = 'wsgi.application'
ASGI_APPLICATION = 'asgi.application'
# ==========================================
# DATABASE CONFIGURATION
# ==========================================


# Décommentez pour MySQL (si nécessaire)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME', default='sofemci_db'),
        'USER': config('DB_USER', default='root'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}


# ==========================================
# PASSWORD VALIDATION
# ==========================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ==========================================
# INTERNATIONALIZATION
# ==========================================
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Abidjan'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# ==========================================
# STATIC FILES & MEDIA
# ==========================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Créez ces dossiers s'ils n'existent pas
STATICFILES_DIRS = [
BASE_DIR / 'static',  # Décommentez quand le dossier existe
]

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Static files finders
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# ==========================================
# DEFAULT PRIMARY KEY
# ==========================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==========================================
# AUTHENTICATION & SESSIONS
# ==========================================
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

# Session configuration
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# ==========================================
# MESSAGES FRAMEWORK
# ==========================================
from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG: 'alert-secondary',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

# ==========================================
# LOGGING CONFIGURATION (optionnel)
# ==========================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'sofemci': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# ==========================================
# SOFEM-CI CUSTOM CONFIGURATION
# ==========================================
SOFEMCI_CONFIG = {
    'COMPANY_NAME': 'SOFEM-CI Industries',
    'VERSION': '2.0.0',
    'MAX_ZONES_EXTRUSION': 50,
    'MAX_MACHINES_PAR_ZONE': 200,
    'OBJECTIF_PRODUCTION_QUOTIDIEN': 75000,  # kg
    'SECTIONS_ACTIVES': ['extrusion', 'imprimerie', 'soudure', 'recyclage'],
    'EQUIPES': ['A', 'B', 'C'],
    'IA_ENABLED': True,
    'MAINTENANCE_PREDICTIVE': True,
}

# ==========================================
# SECURITY SETTINGS FOR PRODUCTION
# ==========================================
if not DEBUG:
    # Security settings
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'
    
    # HSTS settings
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ==========================================
# EMAIL CONFIGURATION (optionnel)
# ==========================================
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Pour développement

# ==========================================
# CACHE CONFIGURATION (optionnel)
# ==========================================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'sofemci-cache',
    }
}

# ==========================================
# DEBUG TOOLBAR (Development only)
# ==========================================
if DEBUG:
    try:
        import debug_toolbar
        INSTALLED_APPS.append('debug_toolbar')
        MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
        
        INTERNAL_IPS = [
            '127.0.0.1',
            'localhost',
        ]
        
        DEBUG_TOOLBAR_CONFIG = {
            'SHOW_TOOLBAR_CALLBACK': lambda request: True,
        }
    except ImportError:
        print("Django Debug Toolbar n'est pas installé. Pour l'installer: pip install django-debug-toolbar")

# ==========================================
# INITIALIZATION CHECKS
# ==========================================
# Create necessary directories
for directory in ['logs', 'media', 'staticfiles']:
    dir_path = BASE_DIR / directory
    dir_path.mkdir(exist_ok=True)

# Créez les dossiers static s'ils n'existent pas
static_dirs = [
    BASE_DIR / 'static',
    BASE_DIR / 'sofemci' / 'static',
]

for static_dir in static_dirs:
    static_dir.mkdir(exist_ok=True)
    # Créez un fichier .gitkeep pour éviter les warnings
    gitkeep_file = static_dir / '.gitkeep'
    if not gitkeep_file.exists():
        gitkeep_file.touch()

# Debug information
if DEBUG:
    print("=== SOFEM-CI CONFIGURATION ===")
    print(f"Version: {SOFEMCI_CONFIG['VERSION']}")
    print(f"Debug Mode: {DEBUG}")
    print(f"Database: {DATABASES['default']['ENGINE']}")
    print(f"Static Dirs créés")
    print("=== CONFIGURATION LOADED ===")