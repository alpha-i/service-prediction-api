import logging

from app import celery
from app import services
from app.entities import TaskStatusTypes

logging.basicConfig(level=logging.DEBUG)


@celery.task(bind=True)
def traing_task(self, upload_code):
    task_code = self.request.id
    datasource = services.datasource.get_by_upload_code(upload_code)
    company_configuration = services.company.get_configuration_for_company_id(datasource.company_id)
    training_task = services.training.create_new_task(
        task_code=task_code,
        datasource_id=datasource.id
    )
    logging.info(training_task)
    services.oracle.train({}, company_configuration)
    services.training.set_task_status(training_task, TaskStatusTypes.successful)
    return


@celery.task
def training_failure(uuid):
    logging.error(f'Training failure for {uuid}')
