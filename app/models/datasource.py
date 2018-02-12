from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from app.db import db
from app.models.base import BaseModel
from enum import Enum
from app.models.customer import Customer


class UploadTypes(Enum):
    FILESYSTEM = 'filesystem'
    BLOBSTORE = 'blobstore'


class DataSource(BaseModel):
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    customer = relationship('Customer')
    upload_code = db.Column(db.String(), index=True)
    type = db.Column(db.Enum(UploadTypes), index=True)
    location = db.Column(db.String(), index=True)
    filename = db.Column(db.String(), nullable=False)

    start_date = db.Column(db.DateTime, index=True, nullable=True)
    end_date = db.Column(db.DateTime, index=True, nullable=True)

    prediction_task_list = relationship('PredictionTask', back_populates='datasource')

    def get_file(self):
        """
        Given the file location and its type, return a reference to that file
        :rtype File
        """
        return open(self.location, 'r')

    @staticmethod
    def get_for_customer(customer_id):
        return DataSource.query.filter(DataSource.customer_id == str(customer_id)).all()

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
