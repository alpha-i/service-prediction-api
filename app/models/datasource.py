from enum import Enum

import pandas as pd
from flask_sqlalchemy import event
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from app.db import db
from app.models import BaseModel, CustomerActionModel, Actions

STORE_INDEX = 'data'


class UploadTypes(Enum):
    FILESYSTEM = 'filesystem'
    BLOBSTORE = 'blobstore'


class DataSourceModel(BaseModel):
    __tablename__ = 'data_source'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = relationship('UserModel', foreign_keys=user_id)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = relationship('CompanyModel', foreign_keys=company_id)
    upload_code = db.Column(db.String(), index=True)
    type = db.Column(db.Enum(UploadTypes), index=True)
    location = db.Column(db.String(), index=True)
    filename = db.Column(db.String(), nullable=False)

    start_date = db.Column(db.DateTime, index=True, nullable=True)
    end_date = db.Column(db.DateTime, index=True, nullable=True)

    prediction_task_list = relationship('PredictionTaskModel', back_populates='datasource')

    def get_file(self):

        with pd.HDFStore(self.location) as hdf_store:
            dataframe = hdf_store[STORE_INDEX]
            return dataframe

    @staticmethod
    def get_for_user(user_id):
        return DataSourceModel.query.filter(DataSourceModel.user_id == str(user_id)).all()

    @staticmethod
    def get_by_upload_code(upload_code):
        try:
            return DataSourceModel.query.filter(DataSourceModel.upload_code == upload_code).one()
        except NoResultFound:
            return None

    @staticmethod
    def generate_filename(upload_code, original_filename):
        return f"{upload_code}_{original_filename}"

    def to_dict(self):
        model_dict = super(DataSourceModel, self).to_dict()
        model_dict.update({'type': self.type.name})
        return model_dict


def update_user_action(mapper, connection, self):
    session = db.create_scoped_session()
    action = CustomerActionModel(
        user_id=self.user_id,
        action=Actions.FILE_UPLOAD
    )
    session.add(action)
    session.commit()


event.listen(DataSourceModel, 'after_insert', update_user_action)
