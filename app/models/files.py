from sqlalchemy.orm.exc import NoResultFound

from app.db import db
from app.models.base import BaseModel
from enum import Enum


class FileTypes(Enum):
    FILESYSTEM = 'filesystem'
    BLOBSTORE = 'blobstore'


class FileUpload(BaseModel):
    customer_id = db.Column(db.String(10), nullable=False, index=True)
    upload_id = db.Column(db.String(), index=True)
    type = db.Column(db.Enum(FileTypes), index=True)
    location = db.Column(db.String(), index=True)

    def get_file(self):
        """
        Given the file location and its type, return a reference to that file
        :rtype File
        """
        return open(self.location, 'r')

    @staticmethod
    def get_for_customer(customer_id):
        return FileUpload.query.filter(FileUpload.customer_id==customer_id).all()

    @staticmethod
    def get_by_upload_id(upload_id):
        try:
            return FileUpload.query.filter(FileUpload.upload_id==upload_id).one()
        except NoResultFound:
            return None

    def to_dict(self):
        model_dict = super(FileUpload, self).to_dict()
        model_dict.update({'type': self.type.name})
        return model_dict
