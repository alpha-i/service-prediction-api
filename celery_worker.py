from app import create_app, make_celery

app = create_app('config', register_blueprints=False)
celery = make_celery(app)
from app.tasks.predict import predict_task

