from app.entities import PredictionTaskEntity, PredictionResultEntity
from app.core.models import Task, Result, TaskStatus


def get_task_by_code(task_code):
    model = PredictionTaskEntity.get_by_task_code(task_code)
    return Task.from_model(model)

def get_result_by_code(task_code):
    model = PredictionResultEntity.get_for_task(task_code)
    return Result.from_model(model)


def insert_task(prediction_task):
    model = prediction_task.to_model()
    model.save()
    return Task.from_model(model)

def update_task(prediction_task):
    model = prediction_task.to_model()
    model.update()
    return Task.from_model(model)


def insert_result(prediction_result):
    model = prediction_result.to_model()
    model.save()
    return Result.from_model(model)

def insert_status(status):
    model = status.to_model()
    model.save()
    return TaskStatus.from_model(model)
