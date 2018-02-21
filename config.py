import os
from dotenv import load_dotenv

load_dotenv(os.getenv('APP_CONFIG'))

DEBUG = eval(os.getenv('DEBUG'))
PORT = int(os.getenv('PORT'))
HOST = os.getenv('HOST')
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND')
SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv('SQLALCHEMY_DATABASE_URI')
SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER')
ALLOWED_EXTENSIONS = eval(os.getenv('ALLOWED_EXTENSIONS'))
SECRET_KEY = os.getenv('SECRET_KEY')
TOKEN_EXPIRATION = int(os.getenv('TOKEN_EXPIRATION'))
HDF5_STORE_INDEX = os.getenv('HDF5_STORE_INDEX')
MAXIMUM_DAYS_FORECAST = int(os.getenv('MAXIMUM_DAYS_FORECAST'))
DEFAULT_EMAIL_FROM_ADDRESS = os.getenv('DEFAULT_EMAIL_FROM_ADDRESS')
MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')
DATE_FORMAT = os.getenv('DATE_FORMAT')
DATETIME_FORMAT = os.getenv('DATETIME_FORMAT')
DATETIME_TZ_FORMAT = os.getenv('DATETIME_TZ_FORMAT')
TARGET_FEATURE = 'number_people'
