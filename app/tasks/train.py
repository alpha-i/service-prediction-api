import logging

from app import celery
from app import services

logging.basicConfig(level=logging.DEBUG)


@celery.task(bind=True)
def traing_task(self, upload_code):
    task_code = self.request.id
    datasource = services.datasource.get_by_upload_code(upload_code)
    training_task = services.training.create_new_task(
        task_code=task_code,
        datasource_id=datasource.id
    )
    services.training.insert(training_task)
    return


@celery.task
def training_failure(uuid):
    logging.error(f'Training failure for {uuid}')
