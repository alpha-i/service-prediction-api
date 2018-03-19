from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from app.db import db
from app.entities import BaseEntity


class TrainingTaskStatusEntity(BaseEntity):
    __tablename__ = 'training_task_status'

    training_task_id = db.Column(db.Integer, db.ForeignKey('training_task.id'), nullable=False)
    training_task = relationship('TrainingTaskEntity', back_populates='statuses')
    state = db.Column(db.String(10), index=True)
    message = db.Column(db.JSON, nullable=True)


class TrainingTaskEntity(BaseEntity):
    __tablename__ = 'training_task'

    INCLUDE_ATTRIBUTES = ('task_code', 'statuses', 'datasource_id', 'datasource', 'status')

    task_code = db.Column(db.String(60), unique=True, nullable=False)
    statuses = relationship('TrainingTaskStatusEntity', cascade='all, delete-orphan')

    datasource_id = db.Column(db.ForeignKey('data_source.id'), nullable=False)
    datasource = relationship('DataSourceEntity', back_populates='training_task_list')

    @staticmethod
    def get_by_task_code(task_code):
        try:
            return TrainingTaskEntity.query.filter(TrainingTaskEntity.task_code == task_code).one()
        except NoResultFound:
            return None

    @property
    def status(self):
        if len(self.statuses):
            return self.statuses[-1].state
