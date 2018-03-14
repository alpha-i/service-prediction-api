import logging

# placeholder until we came up with a general way of validating
# the different oracle configurations
from app.core.utils import import_class
from config import MAXIMUM_DAYS_FORECAST

ORACLE_CONFIG = {
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
}


def get_oracle_for_configuration(company_configuration):
    oracle_class = company_configuration['oracle_class']
    calendar_name = company_configuration['calendar_name']


    try:
        oracle = import_class(oracle_class)
    except ImportError:
        raise ImportError("No available oracle found for %s", oracle_class)

    return oracle(
        calendar_name=calendar_name,
        scheduling_configuration=company_configuration['scheduling'],
        oracle_configuration=company_configuration['oracle']
    )


def make_prediction(prediction_request, data_dict, company_configuration):
    logging.warning("*****")
    logging.warning(prediction_request)
    logging.warning(data_dict)
    logging.warning(company_configuration)
    logging.warning("*****")


    start_time = prediction_request['start_time']
    oracle = get_oracle_for_configuration(company_configuration)
    oracle.config['n_forecast'] = MAXIMUM_DAYS_FORECAST + 2
    oracle.train(data_dict, start_time)
    oracle_prediction_result = oracle.predict(
        data=data_dict,
        current_timestamp=start_time,
        number_of_iterations=1
    )
    return oracle_prediction_result
