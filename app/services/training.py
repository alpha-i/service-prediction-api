from app.core.models import TrainingTask
from app.entities.training import TrainingTaskEntity


def create_new_task(task_code, datasource_id):
    return TrainingTask(
        task_code=task_code,
        datasource_id=datasource_id
    )


def insert(traing_task):
    model = traing_task.to_model()
    model.save()
    return TrainingTask.from_model(model)


def get_for_task_code(task_code):
    model = TrainingTaskEntity.get_by_task_code(task_code)
    return TrainingTask.from_model(model)
