"""
Django settings for ecotrading project.

Generated by 'django-admin startproject' using Django 4.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

from pathlib import Path
from .jazzmin import *
from datetime import timedelta




# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-1@%_-7!z=r9nf#$rbge-n10+fs@9x)q8=b2o0qbl&8)n$%#x0x'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django_crontab',
    'jazzmin',
    'rest_framework',
    'debug_toolbar',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'member',
    'portfolio',
    'stocklist',
    'stockwarehouse',
  
    
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware', 
]

INTERNAL_IPS = ['127.0.0.1', 'localhost']

ROOT_URLCONF = 'ecotrading.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'ecotrading.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES_LIST = [{
#server
      'default': {
         'ENGINE': 'django.db.backends.postgresql',
         'NAME': 'ecotrading',                      
         'USER': 'admin',
         'PASSWORD': 'Ecotr@ding2023',
         'HOST': 'localhost',
         'PORT': '',
     }
 }, 
#localhost
{
     'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ecotrading',                      
        'USER': 'postgres',
        'PASSWORD': 'Ecotr@ding2021',
        'HOST': '',
        'PORT': '5432',
    }
}]
DATABASES = DATABASES_LIST[1]

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Ho_Chi_Minh'

USE_I18N = True

USE_L10N = False

USE_TZ = False

DATE_FORMAT = ( ( 'd-m-Y' ))
DATE_INPUT_FORMATS = ( ('%d-%m-%Y'),)
DATETIME_FORMAT = (( 'd-m-Y H:i' ))
DATETIME_INPUT_FORMATS = (('%d-%m-%Y %H:%i'),)


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = Path.joinpath(BASE_DIR, 'static')
MEDIA_URL = '/media/'
MEDIA_ROOT = Path.joinpath(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
JAZZMIN_SETTINGS = JAZZMIN_SETTINGS
JAZZMIN_UI_TWEAKS = JAZZMIN_UI_TWEAKS

CRONTAB_TIMEZONE = 'Asia/Ho_Chi_Minh'

CRONJOBS = [
    ('40 8 * * 1-5', 'stocklist.logic.filter_stock_daily'), # Chạy lúc 14:59 từ thứ 2 đến thứ 6
    ('30 8 * * 1-5', 'stocklist.auto_news.auto_news_daily'), # Chạy lúc 15:30 từ thứ 2 đến thứ 6
    ('00 12 * * 1-5', 'stocklist.auto_news.auto_news_omo'), # Chạy lúc 17:00 từ thứ 2 đến thứ 6
    ('30 15 * * 1-5', 'portfolio.models.get_all_info_stock_price'), # Chạy lúc 15:30 từ thứ 2 đến thứ 6
    ('00 0 * * 1-5', 'stocklist.logic.check_dividend'),# chạy lúc 7 giờ sáng
    ('00 0 * * 1-5', 'stocklist.check_update_analysis_and_send_notifications'),# chạy lúc 7 giờ sáng
    ('00 0 * * 1-5', 'webdata.save_data'),# chạy lúc 7 giờ sáng
    ('30 0 * * 1-5', 'stocklist.auto_news.auto_news_stock_worlds'),# chạy lúc 7h15 giờ sáng
    ('30 2 * * 1-5', 'stocklist.logic.get_info_stock_price_filter'),# chạy lúc 9h30 sáng
    ('30 4 * * 1-5', 'stocklist.logic.get_info_stock_price_filter'),# chạy lúc 11h30 sáng
    ('00 7 * * 1-5', 'stocklist.logic.get_info_stock_price_filter'),# chạy lúc 14h00 trưa
    ('45 7 * * 1-5', 'stocklist.logic.get_info_stock_price_filter'),# chạy lúc 14h45 trưa

]
