from enum import Enum

from sqlalchemy import event, Column, String, ForeignKey, Integer, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from app.database import db_session, local_session_scope
from app.entities import BaseEntity, CustomerActionEntity, Actions


class TaskStatusTypes(Enum):
    queued = 'QUEUED'
    started = 'STARTED'
    in_progress = 'IN PROGRESS'
    successful = 'SUCCESSFUL'
    failed = 'FAILED'


class PredictionTaskEntity(BaseEntity):
    __tablename__ = 'prediction_task'

    INCLUDE_ATTRIBUTES = ('status', 'statuses', 'prediction_result',
                          'is_completed', 'prediction_request', 'datasource_upload_code')

    name = Column(String(60), nullable=False)

    company_id = Column(ForeignKey('company.id'), nullable=False)
    company = relationship('CompanyEntity', foreign_keys=company_id)

    task_code = Column(String(60), unique=True, nullable=False)
    statuses = relationship('PredictionTaskStatusEntity', cascade='all, delete-orphan')

    datasource_id = Column(Integer, ForeignKey('data_source.id'), nullable=False)
    datasource = relationship('DataSourceEntity', back_populates='prediction_task_list')

    prediction_result = relationship('PredictionResultEntity', uselist=False, back_populates='prediction_task',
                                     cascade='all, delete-orphan')
    prediction_request = Column(JSON)

    @staticmethod
    def get_by_task_code(task_code):
        try:
            prediction_task_entity = PredictionTaskEntity.query.filter(
                PredictionTaskEntity.task_code == task_code).one()
            db_session.refresh(prediction_task_entity)
            return prediction_task_entity
        except NoResultFound:
            return None

    @staticmethod
    def get_by_datasource_id(datasource_id, ):
        return PredictionTaskEntity.query.filter(
            PredictionTaskEntity.datasource_id == datasource_id
        ).order_by(PredictionTaskEntity.last_update.desc()).all()

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

    @property
    def datasource_upload_code(self):
        return self.datasource.upload_code


class PredictionTaskStatusEntity(BaseEntity):
    __tablename__ = 'prediction_task_status'

    prediction_task_id = Column(Integer, ForeignKey('prediction_task.id'), nullable=False)
    prediction_task = relationship('PredictionTaskEntity', back_populates='statuses')
    state = Column(String(), index=True)
    message = Column(String(), nullable=True)


class PredictionResultEntity(BaseEntity):
    __tablename__ = 'prediction_result'

    company_id = Column(Integer, ForeignKey('company.id'), nullable=False)
    company = relationship('CompanyEntity', back_populates='prediction_results')

    task_code = Column(String(60), unique=True)
    result = Column(JSON)

    prediction_task_id = Column(Integer, ForeignKey('prediction_task.id'), nullable=False)
    prediction_task = relationship('PredictionTaskEntity', back_populates='prediction_result')

    @staticmethod
    def get_for_task(task_code):
        try:
            return PredictionResultEntity.query.filter(PredictionResultEntity.task_code == task_code).one()
        except NoResultFound:
            return None


def update_user_action(mapper, connection, self):
    action = CustomerActionEntity(
        company_id=self.company_id,
        action=Actions.PREDICTION_STARTED
    )
    with local_session_scope() as session:
        session.add(action)


event.listen(PredictionTaskEntity, 'after_insert', update_user_action)
