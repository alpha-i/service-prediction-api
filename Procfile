web: gunicorn -b 0.0.0.0:5000 application:app
worker: PYTHONOPTIMIZE=1 celery -A celery_worker.celery worker -E --loglevel=debug
