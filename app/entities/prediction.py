from enum import Enum

from sqlalchemy import event
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from app.db import db
from app.entities import BaseEntity, CustomerActionEntity, Actions


class TaskStatusTypes(Enum):
    queued = 'QUEUED'
    started = 'STARTED'
    successful = 'SUCCESSFUL'
    failed = 'FAILED'


class PredictionTaskEntity(BaseEntity):
    __tablename__ = 'prediction_task'

    INCLUDE_ATTRIBUTES = ('status', 'statuses', 'result', 'datasource', 'is_completed', 'prediction_request')

    name = db.Column(db.String(60), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = relationship('UserEntity', back_populates='tasks')

    task_code = db.Column(db.String(60), unique=True, nullable=False)
    statuses = relationship('PredictionTaskStatusEntity', cascade='all, delete-orphan')

    datasource_id = db.Column(db.Integer, db.ForeignKey('data_source.id'), nullable=False)
    datasource = relationship('DataSourceEntity', back_populates='prediction_task_list')

    prediction_result = relationship('PredictionResultEntity', uselist=False, back_populates='prediction_task',
                                     cascade='all, delete-orphan')
    prediction_request = db.Column(db.JSON)

    @staticmethod
    def get_by_task_code(task_code):
        try:
            return PredictionTaskEntity.query.filter(PredictionTaskEntity.task_code == task_code).one()
        except NoResultFound:
            return None

    @staticmethod
    def get_by_user_id(user_id):
        return PredictionTaskEntity.query.filter(PredictionTaskEntity.user_id == user_id).all()

    @property
    def status(self):
        if len(self.statuses):
            return self.statuses[-1].state
        return None

    @property
    def is_completed(self):
        return self.status in [TaskStatusTypes.successful.value, TaskStatusTypes.failed.value]


class PredictionTaskStatusEntity(BaseEntity):
    __tablename__ = 'prediction_task_status'

    prediction_task_id = db.Column(db.Integer, db.ForeignKey('prediction_task.id'), nullable=False)
    prediction_task = relationship('PredictionTaskEntity', back_populates='statuses')
    state = db.Column(db.String(10), index=True)
    message = db.Column(db.JSON, nullable=True)


class PredictionResultEntity(BaseEntity):
    INCLUDE_ATTRIBUTES = ('prediction_task',)
    __tablename__ = 'prediction_result'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = relationship('UserEntity', back_populates='results')
    task_code = db.Column(db.String(60), unique=True)
    result = db.Column(db.JSON)

    prediction_task_id = db.Column(db.Integer, db.ForeignKey('prediction_task.id'), nullable=False)
    prediction_task = relationship('PredictionTaskEntity', back_populates='prediction_result')

    @staticmethod
    def get_for_task(task_code):
        try:
            return PredictionResultEntity.query.filter(PredictionResultEntity.task_code == task_code).one()
        except NoResultFound:
            return None


def update_user_action(mapper, connection, self):
    session = db.create_scoped_session()
    action = CustomerActionEntity(
        user_id=self.user_id,
        action=Actions.PREDICTION_STARTED
    )
    session.add(action)
    session.commit()


event.listen(PredictionTaskEntity, 'after_insert', update_user_action)
