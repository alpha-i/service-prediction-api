import enum

import pandas as pd
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import event

from app.database import local_session_scope
from app.entities import BaseEntity, CustomerActionEntity, Actions
from config import HDF5_STORE_INDEX


class UploadTypes(enum.Enum):
    FILESYSTEM = 'filesystem'
    BLOBSTORE = 'blobstore'


class DataSourceEntity(BaseEntity):
    INCLUDE_ATTRIBUTES = ('type', 'prediction_task_list')

    __tablename__ = 'data_source'

    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship('UserEntity', foreign_keys=user_id)
    company_id = Column(Integer, ForeignKey('company.id'), nullable=False)
    company = relationship('CompanyEntity', foreign_keys=company_id)
    upload_code = Column(String(), index=True)
    type = Column(Enum(UploadTypes), index=True)
    location = Column(String(), index=True)
    filename = Column(String(), nullable=False)

    start_date = Column(DateTime(timezone=True), index=True, nullable=True)
    end_date = Column(DateTime(timezone=True), index=True, nullable=True)

    prediction_task_list = relationship('PredictionTaskEntity', back_populates='datasource',
                                        cascade='all, delete-orphan')
    training_task_list = relationship('TrainingTaskEntity', back_populates='datasource',
                                      cascade='all, delete-orphan')

    is_original = Column(Boolean, default=False)
    features = Column(String, nullable=True)
    target_feature = Column(String, nullable=True)

    def get_file(self):
        with pd.HDFStore(self.location) as hdf_store:
            dataframe = hdf_store[HDF5_STORE_INDEX]
            return dataframe

    @staticmethod
    def get_for_user(user_id):
        return DataSourceEntity.query.filter(DataSourceEntity.user_id == str(user_id)).all()

    @staticmethod
    def get_by_upload_code(upload_code):
        try:
            return DataSourceEntity.query.filter(DataSourceEntity.upload_code == upload_code).one()
        except NoResultFound:
            return None

    @staticmethod
    def generate_filename(upload_code, original_filename):
        return f"{upload_code}_{original_filename}"


def update_user_action(mapper, connection, self):
    action = CustomerActionEntity(
        company_id=self.company_id,
        user_id=self.user_id,
        action=Actions.FILE_UPLOAD
    )
    with local_session_scope() as session:
        session.add(action)


event.listen(DataSourceEntity, 'after_insert', update_user_action)
