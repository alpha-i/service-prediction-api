import logging

from app import celery
from app import interpreters
from app import services
from app.core.models import PredictionResult
from app.core.schemas import PredictionRequestSchema
from app.core.utils import json_reload
from app.entities import TaskStatusTypes
from app.services.prediction import set_task_status

logging.basicConfig(level=logging.DEBUG)


@celery.task(bind=True)
def training_and_prediction_task(self, task_code, company_id, upload_code, prediction_request):
    uploaded_file = services.datasource.get_by_upload_code(upload_code)
    prediction_task = services.prediction.get_task_by_code(task_code)
    if not uploaded_file:
        logging.warning("No upload could be found for code %s", upload_code)
        return

    prediction_request, errors = PredictionRequestSchema().load(prediction_request)
    logging.info("Prediction request %s received: %s", upload_code, prediction_request)
    if errors:
        logging.warning(errors)
        set_task_status(prediction_task, TaskStatusTypes.failed)
        raise Exception(errors)

    prediction_task = services.prediction.add_prediction_request(
        prediction_task, json_reload(prediction_request))

    logging.info("*** TASK STARTED! %s", prediction_task.task_code)
    set_task_status(prediction_task, TaskStatusTypes.started, message='Task started!')

    data_frame_content = uploaded_file.get_file()
    company = services.company.get_by_id(company_id)
    company_configuration = company.current_configuration

    interpreter = services.company.get_datasource_interpreter(company_configuration)
    data_dict = interpreter.from_dataframe_to_data_dict(data_frame_content)

    set_task_status(
        prediction_task, TaskStatusTypes.in_progress,
        message='Training machine learning model'
    )

    oracle = services.oracle.get_oracle_for_configuration(company_configuration)
    services.oracle.train(
        oracle=oracle,
        prediction_request=prediction_request,
        data_dict=data_dict
    )

    set_task_status(
        prediction_task, TaskStatusTypes.in_progress,
        message='Prediction in progress'
    )
    oracle_prediction_result = services.oracle.predict(
        oracle=oracle,
        prediction_request=prediction_request,
        data_dict=data_dict
    )

    prediction_result_interpreter = interpreters.prediction.get_prediction_interpreter(company_configuration)
    interpreted_prediction_result = prediction_result_interpreter(oracle_prediction_result)

    logging.info("*** TASK FINISHED! %s", prediction_task.task_code)
    set_task_status(prediction_task, TaskStatusTypes.successful)

    prediction_result_model = PredictionResult(
        company_id=company_id,
        task_code=prediction_task.task_code,
        result=json_reload(interpreted_prediction_result),
        prediction_task_id=prediction_task.id
    )

    services.prediction.insert_result(prediction_result_model)
    return


@celery.task
def prediction_failure(context, exc, traceback, task_code, *args, **kwargs):
    prediction_task = services.prediction.get_task_by_code(task_code)
    logging.warning(f"Exception was: {exc}")
    set_task_status(prediction_task, TaskStatusTypes.failed)
    print('Task {0} raised exception: {1!r}\n{2!r}'.format(context, exc, traceback))
