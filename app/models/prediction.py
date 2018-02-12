from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from app.db import db
from app.models.base import BaseModel


class PredictionTask(BaseModel):
    customer_id = db.Column(db.Integer, index=True, nullable=False)
    task_code = db.Column(db.String(60), unique=True, nullable=False)
    status = db.Column(db.String(10), nullable=False)

    upload_id = db.Column(db.Integer, db.ForeignKey('file_upload.id'), nullable=False)
    upload = relationship('FileUpload', back_populates='prediction_task_list')

    prediction_result = relationship('PredictionResult', uselist=False, back_populates='prediction_task')

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


class PredictionResult(BaseModel):
    customer_id = db.Column(db.String)
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
