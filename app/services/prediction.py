from app.models import PredictionTaskModel, PredictionResultModel
from app.core.entities import Task, Result

def get_task_by_code(task_code):
    model = PredictionTaskModel.get_by_task_code(task_code)
    return Task.from_model(model)

def get_result_by_code(task_code):
    model = PredictionResultModel.get_for_task(task_code)
    return Result.from_model(model)
