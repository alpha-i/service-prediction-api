import logging
import uuid

from app import services
from app.core.models import PredictionTask, PredictionResult, PredictionTaskStatus
from app.entities import PredictionTaskEntity, PredictionResultEntity


def get_task_by_code(task_code):
    model = PredictionTaskEntity.get_by_task_code(task_code)
    return PredictionTask.from_model(model)


def get_result_by_code(task_code):
    model = PredictionResultEntity.get_for_task(task_code)
    return PredictionResult.from_model(model)


def insert_task(prediction_task):
    model = prediction_task.to_model()
    model.save()
    return PredictionTask.from_model(model)


def update_task(prediction_task):
    model = prediction_task._model
    prediction_task.refresh()
    for k, v in prediction_task.__dict__.items():
        try:
            setattr(model, k, v)
        except AttributeError:
            logging.debug(f"CANNOT SET {k} to {v}")
    model.update()
    return PredictionTask.from_model(model)


def insert_result(prediction_result):
    model = prediction_result.to_model()
    model.save()
    return PredictionResult.from_model(model)


def insert_status(status):
    model = status.to_model()
    model.save()
    return PredictionTaskStatus.from_model(model)


def set_task_status(task, status, message=None):
    task_status = services.prediction.insert_status(
        PredictionTaskStatus(
            prediction_task_id=task.id,
            state=status.value,
            message=message,
        )
    )
    return task_status


def create_prediction_task(task_name, task_code, company_id, datasource_id):
    task = services.prediction.insert_task(
        PredictionTask(name=task_name,
                       task_code=task_code,
                       company_id=company_id,
                       datasource_id=datasource_id)
    )
    return task


def generate_task_code():
    return str(uuid.uuid4())


def add_prediction_request(prediction_task, prediction_request):
    prediction_task = get_task_by_code(prediction_task.task_code)
    model = prediction_task._model
    model.prediction_request = prediction_request
    model.save()
    return PredictionTask.from_model(model)
