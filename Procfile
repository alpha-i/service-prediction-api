web: uwsgi uwsgi.ini
worker: PYTHONOPTIMIZE=1 celery -A celery_worker.celery worker -E --loglevel=debug
