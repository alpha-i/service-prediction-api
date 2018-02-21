from enum import Enum

import pandas as pd
from flask import current_app
from flask_sqlalchemy import event
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from app.db import db
from app.models.base import BaseModel
# noinspection PyUnresolvedReferences
from app.models.customer import User, CustomerAction, Actions

STORE_INDEX = 'data'


class UploadTypes(Enum):
    FILESYSTEM = 'filesystem'
    BLOBSTORE = 'blobstore'


class DataSource(BaseModel):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = relationship('User')
    upload_code = db.Column(db.String(), index=True)
    type = db.Column(db.Enum(UploadTypes), index=True)
    location = db.Column(db.String(), index=True)
    filename = db.Column(db.String(), nullable=False)

    start_date = db.Column(db.DateTime, index=True, nullable=True)
    end_date = db.Column(db.DateTime, index=True, nullable=True)

    prediction_task_list = relationship('PredictionTask', back_populates='datasource')

    def get_file(self):

        with pd.HDFStore(self.location) as hdf_store:
            dataframe = hdf_store[STORE_INDEX]
            return dataframe

    @staticmethod
    def get_for_user(user_id):
        return DataSource.query.filter(DataSource.user_id == str(user_id)).all()

    @staticmethod
    def get_by_upload_code(upload_code):
        try:
            return DataSource.query.filter(DataSource.upload_code == upload_code).one()
        except NoResultFound:
            return None

    @staticmethod
    def generate_filename(upload_code, original_filename):
        return f"{upload_code}_{original_filename}"

    def to_dict(self):
        model_dict = super(DataSource, self).to_dict()
        model_dict.update({'type': self.type.name})
        return model_dict


def update_user_action(mapper, connection, self):
    session = db.create_scoped_session()
    action = CustomerAction(
        user_id=self.user_id,
        action=Actions.FILE_UPLOAD
    )
    session.add(action)
    session.commit()


event.listen(DataSource, 'after_insert', update_user_action)
