import logging
from enum import Enum

from flask import url_for
from sqlalchemy import event
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from app.db import db
from app.models import BaseModel, CustomerActionModel, Actions


class TaskStatusTypes(Enum):
    queued = 'QUEUED'
    started = 'STARTED'
    successful = 'SUCCESSFUL'
    failed = 'FAILED'


class PredictionTaskModel(BaseModel):
    __tablename__ = 'prediction_task'

    INCLUDE_ATTRIBUTES = ('status', 'statuses', 'result')

    name = db.Column(db.String(60), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = relationship('UserModel', back_populates='tasks')

    task_code = db.Column(db.String(60), unique=True, nullable=False)
    statuses = relationship('TaskStatusModel')

    datasource_id = db.Column(db.Integer, db.ForeignKey('data_source.id'), nullable=False)
    datasource = relationship('DataSourceModel', back_populates='prediction_task_list')

    prediction_result = relationship('PredictionResultModel', uselist=False, back_populates='prediction_task')
    prediction_request = db.Column(db.JSON)

    @staticmethod
    def get_by_task_code(task_code):
        try:
            return PredictionTaskModel.query.filter(PredictionTaskModel.task_code == task_code).one()
        except NoResultFound:
            return None

    @staticmethod
    def get_by_user_id(user_id):
        return PredictionTaskModel.query.filter(PredictionTaskModel.user_id == user_id).all()

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


class TaskStatusModel(BaseModel):
    __tablename__ = 'task_status'

    prediction_task_id = db.Column(db.Integer, db.ForeignKey('prediction_task.id'), nullable=False)
    prediction_task = relationship('PredictionTaskModel', back_populates='statuses')
    state = db.Column(db.String(10), index=True)
    message = db.Column(db.JSON, nullable=True)


class PredictionResultModel(BaseModel):
    __tablename__ = 'prediction_result'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = relationship('UserModel', back_populates='results')
    task_code = db.Column(db.String(60), unique=True)
    result = db.Column(db.JSON)

    prediction_task_id = db.Column(db.Integer, db.ForeignKey('prediction_task.id'), nullable=False)
    prediction_task = relationship('PredictionTaskModel', back_populates='prediction_result')

    @staticmethod
    def get_for_task(task_code):
        try:
            return PredictionResultModel.query.filter(PredictionResultModel.task_code == task_code).one()
        except NoResultFound:
            return None

    def to_dict(self):
        dictionary = super(PredictionResultModel, self).to_dict()
        dictionary['prediction_task'] = self.prediction_task
        return dictionary


def update_user_action(mapper, connection, self):
    session = db.create_scoped_session()
    action = CustomerActionModel(
        user_id=self.user_id,
        action=Actions.PREDICTION_STARTED
    )
    session.add(action)
    session.commit()


event.listen(PredictionTaskModel, 'after_insert', update_user_action)
