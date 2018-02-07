import logging
import time

from celery.result import AsyncResult, allow_join_result

from app import celery
from app.core.oracle import Oracle
from app.core.schemas import prediction_request_schema
from app.db import db
from app.models.files import FileUpload
from app.models.prediction import PredictionTask, PredictionResult


@celery.task(bind=True)
def predict_task(self, customer_id, upload_id, prediction_request):
    prediction_task = create_pending_task(self.request.id, customer_id)
    prediction_request, errors = prediction_request_schema.load(prediction_request)
    if errors:
        raise Exception(errors)
    logging.info("TASK RECEIVED! %s", prediction_task.task_id)
    logging.info("Prediction request: %s")

    data = FileUpload.get_by_id(upload_id)
    if not data:
        set_task_status(prediction_task, 'FAILED')
        return

    time.sleep(5)
    logging.info("TASK STARTED! %s", prediction_task.task_id)
    set_task_status(prediction_task, 'STARTED')
    time.sleep(5)

    # *** TASK ACTION START ***
    # file_contents = data.get_file()
    # file_contents.close()
    data = {
        'features': prediction_request['features'],
        'start_time': prediction_request['start_time'],
        'end_time': prediction_request['end_time']
    }
    prediction = Oracle().predict(data)
    # *** TASK ACTION END *****

    logging.info("TASK FINISHED! %s", prediction_task.task_id)
    set_task_status(prediction_task, 'SUCCESS')

    prediction_result = PredictionResult(
        customer_id=customer_id,
        task_id=prediction_task.task_id,
        result=prediction
    )
    db.session.add(prediction_result)
    db.session.commit()
    return


@celery.task(bind=True)
def prediction_failure(self, uuid):
    result = AsyncResult(uuid)
    with allow_join_result():
        exc = result.get(propagate=False)

    prediction_task = PredictionTask.get_by_task_id(uuid)
    set_task_status(prediction_task, 'FAILED')
    print('Task {0} raised exception: {1!r}\n{2!r}'.format(uuid, exc, result.traceback))


def create_pending_task(task_id, customer_id):
    new_task = PredictionTask(
        task_id=task_id,
        customer_id=customer_id,
        status='QUEUED'
    )
    db.session.add(new_task)
    db.session.commit()
    return new_task


def set_task_status(task, status):
    task.status = status
    db.session.add(task)
    db.session.commit()
