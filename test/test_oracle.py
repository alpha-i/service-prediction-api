import datetime
import logging
import os
import unittest

import pandas as pd
import pytest
from alphai_cromulon_oracle.oracle import CromulonOracle

from app.interpreters.datasource import GymDataSourceInterpreter

logging.basicConfig(level=logging.DEBUG)

EXECUTION_TIME = datetime.datetime(2017, 12, 12, 0)
TEST_DATA_FILE = os.path.join(os.path.dirname(__file__), 'resources/test_full_data.csv')


# We're not using cromulon at the moment, so just skip this test please
@pytest.mark.skip
class TestCromulonIntegration(unittest.TestCase):
    def setUp(self):
        self.config = self.load_gym_config()
        self.data = self.load_test_data()

    def load_test_data(self):
        with open(TEST_DATA_FILE) as csv_file:
            return pd.read_csv(csv_file)

    def load_gym_config(self):
        n_forecasts = 5

        configuration = {
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
            'n_forecasts': n_forecasts,
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

        oracle_config = {
            "scheduling": {
                "prediction_horizon": 240,
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
            "oracle": configuration
        }

        return oracle_config

    def test_cromulon_can_make_a_prediction(self):
        config = self.config

        data_dict = GymDataSourceInterpreter.from_dataframe_to_data_dict(self.data)

        oracle = CromulonOracle(config)
        oracle.train(data_dict, EXECUTION_TIME)

        oracle_prediction = oracle.predict(
            data=data_dict,
            current_timestamp=EXECUTION_TIME,
            number_of_iterations=1
        )

        assert oracle_prediction
