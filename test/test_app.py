from app import create_app, make_celery

APP = create_app('config')
celery = make_celery(APP)
from app.tasks.predict import training_and_prediction_task
celery.tasks.register(training_and_prediction_task)
