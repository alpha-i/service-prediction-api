from sqlalchemy import event, Column, ForeignKey, Integer, String, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from app.database import local_session_scope
from app.entities import BaseEntity, Actions, CustomerActionEntity


class TrainingTaskStatusEntity(BaseEntity):
    __tablename__ = 'training_task_status'

    training_task_id = Column(Integer, ForeignKey('training_task.id'), nullable=False)
    training_task = relationship('TrainingTaskEntity', back_populates='statuses')
    state = Column(String(10), index=True)
    message = Column(JSON, nullable=True)


class TrainingTaskEntity(BaseEntity):
    __tablename__ = 'training_task'

    INCLUDE_ATTRIBUTES = ('task_code', 'statuses', 'datasource_id', 'datasource', 'status')

    task_code = Column(String(60), unique=True, nullable=False)
    statuses = relationship('TrainingTaskStatusEntity', cascade='all, delete-orphan')

    company_id = Column(ForeignKey('company.id'), nullable=False)
    company = relationship('CompanyEntity')

    user_id = Column(ForeignKey('user.id'), nullable=False)
    user = relationship('UserEntity', foreign_keys=user_id)

    datasource_id = Column(ForeignKey('data_source.id'), nullable=False)
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


def update_user_action(mapper, connection, self):
    action = CustomerActionEntity(
        company_id=self.company_id,
        user_id=self.user_id,
        action=Actions.TRAINING_STARTED
    )
    with local_session_scope() as session:
        session.add(action)


event.listen(TrainingTaskEntity, 'after_insert', update_user_action)
