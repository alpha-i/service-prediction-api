import datetime

import pytest

from app import services


@pytest.mark.skip('Waiting for crocubot to be implemented...')
def test_prediction():
    prediction_request = {
        'end_time': datetime.date(2017, 1, 2),
        'feature': 'number_people',
        'name': 'TESTPREDICTION',
        'start_time': datetime.date(2017, 1, 1)
    }

    configuration = {
        # this is the company_configuration.configuration
        'oracle_class': 'alphai_crocubot_oracle.oracle.CrocubotOracle',
        'calendar_name': 'GYMUK',
        'oracle': {
            'universe': {
                'method': "liquidity",
                'n_assets': 10,
                'ndays_window': 10,
                'update_frequency': "weekly",
                'avg_function': "median",
                'dropna': False
            },
            'prediction_horizon': {
                'unit': 'days',
                'value': 1,
            },
            'prediction_delta': {
                'unit': 'days',
                'value': 10,
            },
            'training_delta': {
                'unit': 'days',
                'value': 20,
            },
            'data_transformation': {
                'fill_limit': 5,
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
                'features_ndays': 10,
                'features_resample_minutes': 15,
                'target_delta_ndays': 1,
            },
            'model': {
                'train_path': '/tmp/crocubot',
                'tensorboard_log_path': '/tmp/crocubot',
                'covariance_method': 'Ledoit',
                'covariance_ndays': 100,
                'model_save_path': '/tmp/crocubot',
                'n_training_samples': 15800,
                'INITIAL_ALPHA': 0.05,
                'n_training_samples_benchmark': 1000,
                'n_assets ': 10,
                'classify_per_series ': False,
                'normalise_per_series ': True,
                'use_historical_covariance ': True,
                'n_correlated_series ': 1,
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
                'n_assets': 1,
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
        },
        'scheduling': {
            "prediction_frequency": {
                "frequency_type": "DAILY",
                "days_offset": 0,
                "minutes_offset": 15
            },
            "training_frequency": {
                "frequency_type": "WEEKLY",
                "days_offset": 0,
                "minutes_offset": 15
            },
        },
    }

    data_dict = {}

    services.oracle.predict(prediction_request, data_dict, configuration)
