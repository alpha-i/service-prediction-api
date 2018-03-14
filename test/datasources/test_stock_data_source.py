import os

from flask import url_for
import pandas as pd

import unittest

from app.core.interpreters import StockDataSourceInterpreter, GymDataSourceInterpreter
from test.functional.base_test_class import BaseTestClass

HERE = os.path.join(os.path.dirname(__file__))


class TestStockDataSource(BaseTestClass):
    TESTING = True
    TEST_USER_ID = '99'

    def setUp(self):
        super().setUp()
        self.register_company()
        self.register_user()
        self.login()
        self.set_company_configuration()


    def get_company_configuration(self):
        configuration = {
                # this is the company_configuration.configuration
                'oracle_class': 'alphai_crocubot_oracle.oracle.CrocubotOracle',
                'calendar_name': 'GYMUK',
                'target_feature': 'Returns',
                'datasource_interpreter': 'app.core.interpreters.StockDataSourceInterpreter',
                'prediction_result_interpreter': '',  # TBD
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
        return configuration


    def test_upload_stock_file(self):
        with open(os.path.join(HERE, '../resources/test_stock_standardised.csv'), 'rb') as test_upload_file:
            resp = self.client.post(
                url_for('datasource.upload'),
                content_type='multipart/form-data',
                data={'upload': (test_upload_file, 'test_data.csv')},
                headers={'Accept': 'application/html'}
            )
            assert resp.status_code == 302  # in order to redirect to the dashboard
            assert resp.json



def test_from_oldmutual_csv_to_dataframe():
    with open(os.path.join(HERE, '../resources/test_stock_standardised.csv'), 'rb') as csv_file:
        source_dataframe = StockDataSourceInterpreter.from_csv_to_dataframe(csv_file=csv_file)
    dataframe = StockDataSourceInterpreter.from_dataframe_to_data_dict(source_dataframe)
    assert isinstance(dataframe['Returns'], pd.DataFrame), type(dataframe['Returns'])

def test_from_gymdata_to_dataframe():
    with open(os.path.join(HERE, '../resources/test_full_data.csv'), 'rb') as csv_file:
        source_dataframe = GymDataSourceInterpreter.from_csv_to_dataframe(csv_file)
    dataframe = GymDataSourceInterpreter.from_dataframe_to_data_dict(source_dataframe)
    assert isinstance(dataframe['number_people'], pd.DataFrame), type(dataframe['number_people'])
