import logging
import random

import time

from app import celery
from app.db import db
from app.models.prediction import PredictionTask, PredictionResult


@celery.task(bind=True)
def predict_task(self, customer_id):
    prediction_task = create_pending_task(self.request.id, customer_id)
    logging.info("TASK RECEIVED! %s", prediction_task.task_id)
    time.sleep(5)
    logging.info("TASK STARTED! %s", prediction_task.task_id)
    set_task_status(prediction_task, 'STARTED')
    time.sleep(5)

    result = random.randint(1, 6)

    logging.info("TASK FINISHED! %s", prediction_task.task_id)
    set_task_status(prediction_task, 'SUCCESS')

    prediction_result = PredictionResult(task_id=prediction_task.task_id)
    prediction_result.result = {
        'random': result
    }
    db.session.add(prediction_result)
    db.session.commit()
    return 'Yada yada'


def create_pending_task(task_id, customer_id):
    new_task = PredictionTask(
        task_id=task_id,
        customer_id=customer_id,
        status='PENDING'
    )
    db.session.add(new_task)
    db.session.commit()
    return new_task


def set_task_status(task, status):
    task.status = status
    db.session.add(task)
    db.session.commit()
