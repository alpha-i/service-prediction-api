import logging

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
