from enum import Enum

from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from app.db import db
from app.models.base import BaseModel
from app.models.customer import Customer
from app.models.datasource import DataSource


class TaskStatusTypes(Enum):
    queued = 'QUEUED'
    started = 'STARTED'
    successful = 'SUCCESSFUL'
    failed = 'FAILED'


class PredictionTask(BaseModel):
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    customer = relationship('Customer', back_populates='tasks')

    task_code = db.Column(db.String(60), unique=True, nullable=False)
    statuses = relationship('TaskStatus')

    datasource_id = db.Column(db.Integer, db.ForeignKey('data_source.id'), nullable=False)
    datasource = relationship('DataSource', back_populates='prediction_task_list')

    prediction_result = relationship('PredictionResult', uselist=False, back_populates='prediction_task')
    prediction_request = db.Column(db.JSON)

    @staticmethod
    def get_by_task_code(task_code):
        """
        :return: PredictionTask the prediction
        """
        try:
            return PredictionTask.query.filter(PredictionTask.task_code == task_code).one()
        except NoResultFound:
            return None

    @staticmethod
    def get_by_customer_id(customer_id):
        return PredictionTask.query.filter(PredictionTask.customer_id == customer_id).all()

    def to_dict(self):
        # TODO: switch to marshmallow serialize
        retvalue = super(PredictionTask, self).to_dict()
        if len(self.statuses):
            retvalue['status'] = self.statuses[-1].state
            retvalue['statuses'] = self.statuses
        return retvalue


class TaskStatus(BaseModel):
    prediction_task_id = db.Column(db.Integer, db.ForeignKey('prediction_task.id'))
    prediction_task = relationship('PredictionTask', back_populates='statuses')
    state = db.Column(db.String(10), index=True)
    message = db.Column(db.JSON, nullable=True)


class PredictionResult(BaseModel):
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    customer = relationship('Customer', back_populates='results')
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
