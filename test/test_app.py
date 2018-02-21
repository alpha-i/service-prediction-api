from app import create_app, make_celery

APP = create_app('config')
celery = make_celery(APP)
