from app import create_app, make_celery

app = create_app('config', register_blueprints=False)
celery = make_celery(app)
from app.tasks.predict import training_and_prediction_task
celery.tasks.register(training_and_prediction_task)
