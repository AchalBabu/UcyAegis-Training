"""
Django settings for Ucyaegis Training project.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: change this before deploying to production!
SECRET_KEY = 'django-insecure-change-this-secret-key-in-production-ucyaegis'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Local apps
    'accounts',
    'courses',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ucyaegis.urls'

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

WSGI_APPLICATION = 'ucyaegis.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Where to send users after login (overridden per-view, kept as fallback)
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# ---------------------------------------------------------------------------
# PAYMENT GATEWAY — RAZORPAY (UPI only, fully automatic)
# ---------------------------------------------------------------------------
# 1. Sign up at https://dashboard.razorpay.com/ (free)
# 2. Settings -> API Keys -> Generate Test Key (for testing) or Live Key
#    (needs KYC approval) for real payments
# 3. Paste the Key Id and Key Secret below
# 4. Checkout is configured (see templates/courses/payment.html) to show
#    ONLY the UPI payment option — no cards/netbanking/wallets shown.
#    Payment is verified automatically via signature check, so the course
#    unlocks the moment a real payment succeeds — no manual approval.
#
# TEST MODE UPI (works only with a Test Key, never charges real money):
#   Use the Razorpay Test UPI VPA:  success@razorpay
#   (any UPI ID ending differently, e.g. failure@razorpay, simulates a
#   failed payment for testing)
# ---------------------------------------------------------------------------
RAZORPAY_KEY_ID = 'rzp_test_TbpQFMCkCQzrDi'       # <-- put your Key Id here
RAZORPAY_KEY_SECRET = 'nJhbhRJjvD2OvpVUDLMzX0np'      # <-- put your Key Secret here

