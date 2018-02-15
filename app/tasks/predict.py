import datetime
import logging
import time

from alphai_cromulon_oracle.oracle import CromulonOracle
from alphai_delphi.oracle.oracle_configuration import OracleConfiguration
from celery.result import AsyncResult, allow_join_result

from app import celery
from app.core.interpreters import datasource_interpreter, prediction_interpreter
from app.core.schemas import prediction_request_schema
from app.core.utils import json_reload
from app.db import db
from app.models.datasource import DataSource
from app.models.prediction import PredictionTask, PredictionResult, TaskStatus, TaskStatusTypes
from config import MAXIMUM_DAYS_FORECAST


logging.basicConfig(level=logging.DEBUG)

oracle_config = OracleConfiguration({
    "scheduling": {
        "prediction_horizon": 24,
        "prediction_frequency":
            {
                "frequency_type": "DAILY",
                "days_offset": 0,
                "minutes_offset": 15
            },
        "prediction_delta": 10,

        "training_frequency":
            {
                "frequency_type": "WEEKLY",
                "days_offset": 0,
                "minutes_offset": 15
            },
        "training_delta": 20,
    },
    "oracle": {
        'nassets': 1,
        'data_transformation': {
            'fill_limit': 5,
            'holiday_calendar': 'NYSE',
            'feature_config_list': [
                {
                    'name': 'number_people',
                    'normalization': 'standard',
                    'length': 50,
                    'is_target': True
                },
                {
                    'name': 'temperature',
                    'normalization': 'standard',
                    'length': 50
                },
            ],
            'target_config_list': [
                {
                    'name': 'number_people',
                    'length': 5
                },
            ],
            'data_name': 'GYM',
            'features_ndays': 10,
            'features_resample_minutes': 15,
            'target_delta_ndays': 1,
        },
        'train_path': '/tmp/cromulon/',
        'model_save_path': '/tmp/cromulon/',
        'tensorboard_log_path': '/tmp/cromulon/',
        'd_type': 'float32',
        'tf_type': 32,
        'random_seed': 0,
        'predict_single_shares': False,
        'classify_per_series': True,
        'normalise_per_series': True,

        # Training specific
        'n_epochs': 1,
        'n_retrain_epochs': 1,
        'learning_rate': 2e-3,
        'batch_size': 100,
        'cost_type': 'bayes',
        'n_train_passes': 32,
        'n_eval_passes': 32,
        'resume_training': False,
        'use_gpu': False,  # my macbook doesn't have a GPU :(((

        # Topology
        'n_series': 1,
        'do_kernel_regularisation': True,
        'do_batch_norm': False,
        'n_res_blocks': 6,
        'n_features_per_series': 271,
        'n_forecasts': 5,  # WE HAVE TO CHANGE THIS
        'n_classification_bins': 12,
        'layer_heights': [400, 400, 400, 400],
        'layer_widths': [1, 1, 1, 1],
        'layer_types': ['conv', 'res', 'full', 'full'],
        'activation_functions': ['relu', 'relu', 'relu', 'relu'],

        # Initial conditions
        'INITIAL_WEIGHT_UNCERTAINTY': 0.02,
        'INITIAL_BIAS_UNCERTAINTY': 0.02,
        'INITIAL_WEIGHT_DISPLACEMENT': 0.1,
        'INITIAL_BIAS_DISPLACEMENT': 0.1,
        'USE_PERFECT_NOISE': False,

        # Priors
        'double_gaussian_weights_prior': True,
        'wide_prior_std': 1.0,
        'narrow_prior_std': 0.001,
        'spike_slab_weighting': 0.6
    }
})


@celery.task(bind=True)
def predict_task(self, customer_id, upload_code, prediction_request):
    uploaded_file = DataSource.get_by_upload_code(upload_code)  # type: DataSource
    if not uploaded_file:
        logging.warning("No upload could be found for code %s", upload_code)
        return

    prediction_task = create_task(self.request.id, customer_id, uploaded_file.id)
    set_task_status(prediction_task, TaskStatusTypes.queued)
    prediction_request, errors = prediction_request_schema.load(prediction_request)

    if errors:
        logging.warning(errors)
        raise Exception(errors)

    prediction_task.prediction_request = json_reload(prediction_request)

    db.session.add(prediction_task)
    db.session.commit()

    logging.info("Prediction request %s received: %s", upload_code, prediction_request)

    time.sleep(1)
    logging.info("*** TASK STARTED! %s", prediction_task.task_code)
    set_task_status(prediction_task, TaskStatusTypes.started)

    start_time = prediction_request['start_time']
    end_time = prediction_request['end_time']


    oracle_config.oracle['n_forecasts'] = MAXIMUM_DAYS_FORECAST + 2

    # *** TASK ACTION START ***
    data_frame_content = uploaded_file.get_file()
    data_dict = datasource_interpreter(data_frame_content)
    oracle = CromulonOracle(oracle_config)

    oracle.train(data_dict, start_time)
    oracle_prediction_result = oracle.predict(
        data=data_dict,
        current_timestamp=start_time,
        number_of_iterations=1
    )

    prediction_result = prediction_interpreter(oracle_prediction_result)
    # *** TASK ACTION END *****

    logging.info("*** TASK FINISHED! %s", prediction_task.task_code)
    set_task_status(prediction_task, TaskStatusTypes.successful)

    prediction_result = PredictionResult(
        customer_id=customer_id,
        task_code=prediction_task.task_code,
        result=json_reload(prediction_result),
        prediction_task_id=prediction_task.id
    )
    db.session.add(prediction_result)
    db.session.commit()
    return


@celery.task
def prediction_failure(uuid):
    result = AsyncResult(uuid)
    with allow_join_result():
        exc = result.get(propagate=False)
        print(exc)

    prediction_task = PredictionTask.get_by_task_code(uuid)
    set_task_status(prediction_task, TaskStatusTypes.failed)
    print('Task {0} raised exception: {1!r}\n{2!r}'.format(uuid, exc, result.traceback))


def create_task(task_code, customer_id, upload_code):
    new_task = PredictionTask(
        task_code=task_code,
        customer_id=customer_id,
        datasource_id=upload_code
    )
    db.session.add(new_task)
    db.session.commit()
    return new_task


def set_task_status(task, status):
    status_model = TaskStatus(
        prediction_task_id=task.id,
        state=status.value
    )
    db.session.add(status_model)
    db.session.commit()
