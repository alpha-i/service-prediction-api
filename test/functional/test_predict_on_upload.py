import logging
import os

import time
from flask import url_for

from app.db import db
from app.entities import TaskStatusTypes
from test.functional.base_test_class import BaseTestClass

HERE = os.path.join(os.path.dirname(__file__))


class TestTriggerTaskOnUpload(BaseTestClass):
    TESTING = True
    DB = db

    COMPANY_CONFIGURATION = {
        # 'oracle_class': 'test.mock_oracle.MockMetaCrocubot',
        'oracle_class': 'alphai_metacrocubot_oracle.oracle.MetaCrocubotOracle',
        'calendar_name': 'JSEEOM',
        'target_feature': 'Returns',
        'datasource_interpreter': 'StockDataSourceInterpreter',
        'prediction_result_interpreter': 'app.interpreters.prediction.metacrocubot_prediction_interpreter',
        'upload_strategy': 'TrainAndPredictOnUploadStrategy',
        'oracle': {
            'prediction_horizon': {
                'unit': 'days',
                'value': 1,
            },
            'prediction_delta': {
                'unit': 'days',
                'value': 3,
            },
            'training_delta': {
                'unit': 'days',
                'value': 12,
            },
            'data_transformation': {
                'fill_limit': 5,
                'feature_config_list': [
                    {
                        'name': 'Returns',
                        'transformation': {
                            'name': 'value'
                        },
                        'normalization': None,
                        'local': False,
                        'length': 5,
                        'is_target': True
                    },
                ],
                'features_ndays': 5,
                'features_resample_minutes': 15,
            },
            "model": {
                'train_path': '/tmp/crocubot',
                'covariance_method': 'NERCOME',
                'covariance_ndays': 9,
                'model_save_path': '/tmp/crocubot',
                'tensorboard_log_path': '/tmp/crocubot',
                'd_type': 'float32',
                'tf_type': 32,
                'random_seed': 0,

                # Training specific
                'predict_single_shares': True,
                'n_epochs': 1,
                'n_retrain_epochs': 1,
                'learning_rate': 2e-3,
                'batch_size': 100,
                'cost_type': 'bayes',
                'n_train_passes': 30,
                'n_eval_passes': 100,
                'resume_training': True,
                'classify_per_series': False,
                'normalise_per_series': False,
                'use_gpu': False,

                # Topology
                'n_series': 324,
                'n_assets': 324,
                'n_correlated_series': 1,
                'n_features_per_series': 271,
                'n_forecasts': 1,
                'n_classification_bins': 12,
                'layer_heights': [270, 270],
                'layer_widths': [3, 3],
                'activation_functions': ['relu', 'relu'],

                # Initial conditions
                'INITIAL_ALPHA': 0.2,
                'INITIAL_WEIGHT_UNCERTAINTY': 0.4,
                'INITIAL_BIAS_UNCERTAINTY': 0.4,
                'INITIAL_WEIGHT_DISPLACEMENT': 0.1,
                'INITIAL_BIAS_DISPLACEMENT': 0.4,
                'USE_PERFECT_NOISE': True,

                # Priors
                'double_gaussian_weights_prior': False,
                'wide_prior_std': 1.2,
                'narrow_prior_std': 0.05,
                'spike_slab_weighting': 0.5,
            }
        },
        'scheduling': {
            'prediction_frequency': {
                'frequency_type': 'MONTHLY',
                'days_offset': -1,
                'minutes_offset': 0
            },
            'training_frequency': {
                'frequency_type': 'MONTHLY',
                'days_offset': -1,
                'minutes_offset': 0
            },
        },
    }

    def setUp(self):
        super().setUp()
        self.create_superuser()
        self.login_superuser()
        self.register_company()
        self.register_user()
        self.set_company_configuration()
        self.logout()

    def test_predict_on_upload_strategy(self):
        self.login()
        with open(os.path.join(HERE, '../resources/test_stock_standardised.csv'), 'rb') as test_upload_file:
            resp = self.client.post(
                url_for('datasource.upload'),
                content_type='multipart/form-data',
                data={'upload': (test_upload_file, 'test_stock_standardised.csv')},
            )

            assert resp.status_code == 201
            upload_code = resp.json['upload_code']
            assert upload_code

        time.sleep(3)

        status = None
        while status not in [TaskStatusTypes.successful.value, TaskStatusTypes.failed.value]:
            resp = self.client.get(
                url_for('prediction.get_tasks')
            )
            status = resp.json[0]['status']
            logging.warning(status)
            time.sleep(1)


        prediction_results = self.client.get(url_for('prediction.get_results'))
        assert len(prediction_results.json) == 1

        assert prediction_results.json[0]['result']['datapoints'][0]['prediction']
        assert prediction_results.json[0]['result']['factors']
        assert prediction_results.json[0]['task_code']
