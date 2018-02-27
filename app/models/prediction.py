import logging
from enum import Enum

from flask import url_for
from sqlalchemy import event
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from app.db import db
from app.models import BaseModel, CustomerAction, Actions


class TaskStatusTypes(Enum):
    queued = 'QUEUED'
    started = 'STARTED'
    successful = 'SUCCESSFUL'
    failed = 'FAILED'


class PredictionTask(BaseModel):
    INCLUDE_ATTRIBUTES = ('status', 'statuses', 'result')

    name = db.Column(db.String(60), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = relationship('User', back_populates='tasks')

    task_code = db.Column(db.String(60), unique=True, nullable=False)
    statuses = relationship('TaskStatus')

    datasource_id = db.Column(db.Integer, db.ForeignKey('data_source.id'), nullable=False)
    datasource = relationship('DataSource', back_populates='prediction_task_list')

    prediction_result = relationship('PredictionResult', uselist=False, back_populates='prediction_task')
    prediction_request = db.Column(db.JSON)

    @staticmethod
    def get_by_task_code(task_code):
        try:
            return PredictionTask.query.filter(PredictionTask.task_code == task_code).one()
        except NoResultFound:
            return None

    @staticmethod
    def get_by_user_id(user_id):
        return PredictionTask.query.filter(PredictionTask.user_id == user_id).all()

    @property
    def status(self):
        if len(self.statuses):
            return self.statuses[-1].state
        return None

    @property
    def result(self):
        logging.warning(self.status)
        if self.status in [TaskStatusTypes.successful.value, TaskStatusTypes.failed.value]:
            return url_for('prediction.result', task_code=self.task_code, _external=True)
        return None


class TaskStatus(BaseModel):
    prediction_task_id = db.Column(db.Integer, db.ForeignKey('prediction_task.id'), nullable=False)
    prediction_task = relationship('PredictionTask', back_populates='statuses')
    state = db.Column(db.String(10), index=True)
    message = db.Column(db.JSON, nullable=True)


class PredictionResult(BaseModel):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = relationship('User', back_populates='results')
    task_code = db.Column(db.String(60), unique=True)
    result = db.Column(db.JSON)

    prediction_task_id = db.Column(db.Integer, db.ForeignKey('prediction_task.id'), nullable=False)
    prediction_task = relationship('PredictionTask', back_populates='prediction_result')

    @staticmethod
    def get_for_task(task_code):
        try:
            return PredictionResult.query.filter(PredictionResult.task_code == task_code).one()
        except NoResultFound:
            return None

    def to_dict(self):
        dictionary = super(PredictionResult, self).to_dict()
        dictionary['prediction_task'] = self.prediction_task
        return dictionary


def update_user_action(mapper, connection, self):
    session = db.create_scoped_session()
    action = CustomerAction(
        user_id=self.user_id,
        action=Actions.PREDICTION_STARTED
    )
    session.add(action)
    session.commit()


event.listen(PredictionTask, 'after_insert', update_user_action)
