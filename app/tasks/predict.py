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
def predict_task(self, customer_id, upload_code, prediction_request):

    uploaded_file = FileUpload.get_by_upload_code(upload_code)
    if not uploaded_file:
        logging.warning("No upload could be found for code %s", upload_code)
        return

    prediction_task = create_pending_task(self.request.id, customer_id, uploaded_file.id)
    prediction_request, errors = prediction_request_schema.load(prediction_request)

    if errors:
        logging.warning(errors)
        raise Exception(errors)

    logging.info("Prediction request %s received: %s", upload_code, prediction_request)

    time.sleep(1)
    logging.info("*** TASK STARTED! %s", prediction_task.task_code)
    set_task_status(prediction_task, 'STARTED')

    # *** TASK ACTION START ***
    # file_contents = data.get_file()
    # file_contents.close()
    time.sleep(1)
    data = {
        'features': prediction_request['features'],
        'start_time': prediction_request['start_time'],
        'end_time': prediction_request['end_time']
    }
    prediction = Oracle().predict(data)
    # *** TASK ACTION END *****

    logging.info("*** TASK FINISHED! %s", prediction_task.task_code)
    set_task_status(prediction_task, 'SUCCESS')

    prediction_result = PredictionResult(
        customer_id=customer_id,
        task_code=prediction_task.task_code,
        result=prediction,
        prediction_task_id=prediction_task.id
    )
    db.session.add(prediction_result)
    db.session.commit()
    return


@celery.task
def prediction_failure(uuid):
    result = AsyncResult(uuid)
    with allow_join_result():
        exc = result.get(propagate=False)
        print(exc)

    prediction_task = PredictionTask.get_by_task_code(uuid)
    set_task_status(prediction_task, 'FAILED')
    print('Task {0} raised exception: {1!r}\n{2!r}'.format(uuid, exc, result.traceback))


def create_pending_task(task_code, customer_id, upload_id):
    new_task = PredictionTask(
        task_code=task_code,
        customer_id=customer_id,
        status='QUEUED',
        upload_id=upload_id
    )
    db.session.add(new_task)
    db.session.commit()
    return new_task


def set_task_status(task, status):
    task.status = status
    db.session.add(task)
    db.session.commit()


def set_task_file(task, upload_file):
    task.upload_id = upload_file.id
    db.session.add(task)
    db.session.commit()
