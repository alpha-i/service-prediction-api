from celery import Task

from app.database import db_session


class BaseDBTask(Task):

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        db_session.remove()

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        db_session.remove()
