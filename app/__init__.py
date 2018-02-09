from celery import Celery
from flask import Flask
from flask_migrate import Migrate

from app.core.utils import CustomJSONEncoder
from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

celery = Celery(__name__, broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)


def create_app(config_filename, register_blueprints=True):
    app = Flask(__name__, static_folder='templates')
    app.url_map.strict_slashes = False
    app.config.from_object(config_filename)
    migrate = Migrate()

    # Init Flask-SQLAlchemy
    from app.db import db
    db.init_app(app)
    migrate.init_app(app, db)

    if register_blueprints:
        from app.views.main import home_blueprint
        from app.views.predict import predict_blueprint
        from app.views.customer import customer_blueprint
        from app.views.upload import upload_blueprint
        from app.views.authentication import authentication_blueprint
        app.register_blueprint(home_blueprint, url_prefix='/')
        app.register_blueprint(predict_blueprint, url_prefix='/predict')
        app.register_blueprint(customer_blueprint, url_prefix='/customer')
        app.register_blueprint(upload_blueprint, url_prefix='/upload')
        app.register_blueprint(authentication_blueprint, url_prefix='/auth')
    app.json_encoder = CustomJSONEncoder
    return app


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=CELERY_RESULT_BACKEND,
        broker=CELERY_BROKER_URL
    )
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery
