# TODO: Change this config to get parameters from the environment

DEBUG = True
PORT = 5000
HOST = "0.0.0.0"
CELERY_BROKER_URL = 'redis://localhost:6379/'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = 'postgresql://localhost:5432/database'