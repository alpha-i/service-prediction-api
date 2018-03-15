import logging
import time

from celery.result import AsyncResult, allow_join_result

from app import celery
from app import services
from app import interpreters
from app.core.models import Task, Result, TaskStatus
from app.core.schemas import prediction_request_schema
from app.core.utils import json_reload
from app.entities import TaskStatusTypes
from config import MAXIMUM_DAYS_FORECAST

logging.basicConfig(level=logging.DEBUG)


@celery.task(bind=True)
def predict_task(self, user_id, upload_code, prediction_request):
    uploaded_file = services.datasource.get_by_upload_code(upload_code)
    if not uploaded_file:
        logging.warning("No upload could be found for code %s", upload_code)
        return

    prediction_task = create_task(self.request.id, user_id, uploaded_file.id, prediction_request['name'])
    set_task_status(prediction_task, TaskStatusTypes.queued)

    prediction_request, errors = prediction_request_schema.load(prediction_request)
    if errors:
        logging.warning(errors)
        raise Exception(errors)

    prediction_task.prediction_request = json_reload(prediction_request)
    prediction_task = services.prediction.update_task(prediction_task)

    logging.info("Prediction request %s received: %s", upload_code, prediction_request)

    time.sleep(1)
    logging.info("*** TASK STARTED! %s", prediction_task.task_code)
    set_task_status(prediction_task, TaskStatusTypes.started)

    data_frame_content = uploaded_file.get_file()
    company_configuration = services.company.get_configuration_for_company_id(uploaded_file.company_id)
    oracle = services.oracle.get_oracle_for_configuration(company_configuration)
    oracle.config['n_forecast'] = MAXIMUM_DAYS_FORECAST + 2
    interpreter = services.company.get_datasource_interpreter(company_configuration)
    data_dict = interpreter.from_dataframe_to_data_dict(data_frame_content)

    oracle_prediction_result = services.oracle.make_prediction(
        prediction_request=prediction_request,
        data_dict=data_dict,
        company_configuration=company_configuration.configuration
    )
    prediction_result = interpreters.prediction.prediction_interpreter(oracle_prediction_result)

    logging.info("*** TASK FINISHED! %s", prediction_task.task_code)
    set_task_status(prediction_task, TaskStatusTypes.successful)

    prediction_result = Result(
        user_id=user_id,
        task_code=prediction_task.task_code,
        result=json_reload(prediction_result),
        prediction_task_id=prediction_task.id
    )

    services.prediction.insert_result(prediction_result)
    return


@celery.task
def prediction_failure(uuid):
    result = AsyncResult(uuid)
    with allow_join_result():
        exc = result.get(propagate=False)
        print(exc)

    prediction_task = services.prediction.get_task_by_code(uuid)
    set_task_status(prediction_task, TaskStatusTypes.failed)
    print('Task {0} raised exception: {1!r}\n{2!r}'.format(uuid, exc, result.traceback))


def create_task(task_code, user_id, upload_code, name):
    return services.prediction.insert_task(
        Task(task_code=task_code,
             user_id=user_id,
             datasource_id=upload_code,
             name=name)
    )


def set_task_status(task, status):
    services.prediction.insert_status(
        TaskStatus(
            prediction_task_id=task.id,
            state=status.value
        )
    )
