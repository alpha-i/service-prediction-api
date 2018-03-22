import abc
import datetime
import logging

from app.core.models import DataSource, CompanyConfiguration


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
        from app.tasks.predict import training_and_prediction_task, prediction_failure

        now = datetime.datetime.now().isoformat()
        upload_code = datasource.upload_code
        company_id = company_configuration.company_id

        # Make up a prediction request
        prediction_request = {
            'name': f'TRAIN-AUTO-{now}',
            'start_time': datasource.end_date,
            'end_time': now,
        }

        async_training_and_prediction_task = training_and_prediction_task.apply_async(
            (company_id, upload_code, prediction_request),
            link_error=prediction_failure.s()
        )

        logging.debug(
            f"Automatically triggered train task for company id {company_id}, with code {async_training_and_prediction_task.id}"
        )
