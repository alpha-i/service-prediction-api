import abc
import datetime
import logging

from app import services
from app.core.models import DataSource, CompanyConfiguration
from app.entities import TaskStatusTypes
from config import MAXIMUM_DAYS_FORECAST


class AbstractUploadStrategy(metaclass=abc.ABCMeta):
    """
    Customers often require a specific approach to the way they use the platform
    to produce predictions. Most of the time the typical flow involves a datasource upload,
    a manually triggered training task and then a prediction on request. Other times they might
    want to submit a specific prediction request automatically, as soon as the upload is complete.

    The goal of a strategy is to make this behaviour easily configurable on a customer basis.
    """

    @abc.abstractmethod
    def run(self, datasource: DataSource, company_configuration: CompanyConfiguration):
        raise NotImplementedError


class OnDemandPredictionStrategy(AbstractUploadStrategy):
    """
    The default strategy: we won't do anything.
    """

    def run(self, datasource: DataSource, company_configuration: CompanyConfiguration):
        pass


class TrainAndPredictOnUploadStrategy(AbstractUploadStrategy):
    """
    If we select this strategy, after a file upload we'll trigger a train-predict immediately
    """

    def run(self, datasource: DataSource, company_configuration: CompanyConfiguration):
        from app.tasks.predict import training_and_prediction_task

        now = datetime.datetime.now().isoformat()
        datasource_id = datasource.id
        datasource_upload_code = datasource.upload_code
        user_id = datasource.user_id
        company_id = company_configuration.company_id

        # Make up a prediction request
        prediction_request = {
            'name': f'ON-UPLOAD-PREDICTION-{now}',
            'start_time': datasource.end_date,
            'end_time': datasource.end_date + datetime.timedelta(days=MAXIMUM_DAYS_FORECAST),
        }
        task_code = services.prediction.generate_task_code()

        prediction_task = services.prediction.create_prediction_task(
            task_name=prediction_request['name'],
            task_code=task_code,
            company_id=company_id,
            user_id=user_id,
            datasource_id=datasource_id,
        )
        services.prediction.set_task_status(prediction_task, TaskStatusTypes.queued)

        training_and_prediction_task.apply_async(
            (task_code, company_id, datasource_upload_code, prediction_request)
        )

        logging.debug(
            f"Automatically triggered train task for company id {company_id}, with code {task_code}"
        )

