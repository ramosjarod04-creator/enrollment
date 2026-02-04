import os
import dj_database_url
from pathlib import Path
from dotenv import load_dotenv

# 1. Setup paths and env
load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Security Settings
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-fallback-key')
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# Allow the main Vercel domain and your specific project URL
ALLOWED_HOSTS = ['.vercel.app', 'now.sh', '127.0.0.1', 'localhost', 'enrollment-silk.vercel.app']

# 3. Application Definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'enrollments', 
    'crispy_forms',
    'crispy_bootstrap5',  # Ensure this matches your CSS framework
    'widget_tweaks',
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # WhiteNoise must be above SessionMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'enrollment_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

# 4. Database - Optimized for Vercel + Neon/Postgres
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        ssl_require=not DEBUG
    )
}

# 5. Static Files & WhiteNoise
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Using CompressedStaticFilesStorage prevents the "Missing File" error 
# that happens with ManifestStorage if a file is referenced but not found.
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# 6. Localization
TIME_ZONE = 'Asia/Manila'
USE_TZ = True

# 7. Auth Redirects
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'