from sqlalchemy.orm.exc import NoResultFound

from app.db import db
from app.models.base import BaseModel


class PredictionTask(BaseModel):
    customer_id = db.Column(db.Integer, index=True, nullable=False)
    task_id = db.Column(db.String(60), unique=True, nullable=False)
    status = db.Column(db.String(10), nullable=False)

    @staticmethod
    def get_by_task_id(task_id):
        """
        :return: PredictionTask the prediction
        """
        try:
            return PredictionTask.query.filter(PredictionTask.task_id == task_id).one()
        except NoResultFound:
            return None

    @staticmethod
    def get_by_customer_id(customer_id):
        return PredictionTask.query.filter(PredictionTask.customer_id == customer_id).all()


class PredictionResult(BaseModel):
    task_id = db.Column(db.String(60), unique=True)
    result = db.Column(db.JSON)

    @staticmethod
    def get_for_task(task_id):
        try:
            return PredictionResult.query.filter(PredictionResult.task_id==task_id).one()
        except NoResultFound:
            return None
