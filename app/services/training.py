from app.core.models import TrainingTask, TrainingTaskStatus
from app.entities import TaskStatusTypes
from app.entities.training import TrainingTaskEntity, TrainingTaskStatusEntity


def create_new_task(task_code, company_id, datasource_id):
    training_task = TrainingTask(
        task_code=task_code,
        company_id=company_id,
        datasource_id=datasource_id
    )
    training_task = insert(training_task)
    create_task_status(training_task.id, TaskStatusTypes.queued)
    return training_task


def insert(traing_task):
    model = traing_task.to_model()
    model.save()
    return TrainingTask.from_model(model)


def get_for_task_code(task_code):
    model = TrainingTaskEntity.get_by_task_code(task_code)
    return TrainingTask.from_model(model)


def create_task_status(task_id, state, message=None):
    training_task_status = TrainingTaskStatusEntity(
        training_task_id=task_id,
        state=state.value,
        message=message
    )
    training_task_status.save()
    return TrainingTaskStatus.from_model(training_task_status)


def set_task_status(training_task, status, message=None):
    training_task_status = TrainingTaskStatusEntity(
        training_task_id=training_task.id,
        state=status.value,
        message=message
    )
    training_task_status.save()
    return training_task_status
