# TODO: Change this config to get parameters from the environment
import os

DEBUG = True
PORT = 5000
HOST = "0.0.0.0"
CELERY_BROKER_URL = 'redis://localhost:6379/'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = 'postgresql://localhost:5432/database'
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')  # changeme!
ALLOWED_EXTENSIONS = {'csv'}
SECRET_KEY = 'DcNKg9UgXG14kBw2BQYgfVrkq6ZICr7S'
TOKEN_EXPIRATION = 3600  # seconds
HDF5_STORE_INDEX = 'data'
MAXIMUM_DAYS_FORECAST = 30
