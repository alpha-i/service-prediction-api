import json
import os

from flask import url_for
from flask_testing import TestCase

from app.db import db
from app.services.superuser import create_admin
from app.services.user import generate_confirmation_token
from config import SUPERUSER_EMAIL, SUPERUSER_PASSWORD
from test.test_app import APP


class BaseTestClass(TestCase):
    TESTING = True
    DB = db

    SUPERUSER_EMAIL = SUPERUSER_EMAIL
    SUPERUSER_PASSWORD = SUPERUSER_PASSWORD
    USER_EMAIL = 'test_user@email.com'
    USER_PASSWORD = 'password'

    COMPANY_CONFIGURATION = {
        # 'oracle_class': 'test.mock_oracle.MockMetaCrocubot',
        'oracle_class': 'alphai_metacrocubot_oracle.oracle.MetaCrocubotOracle',
        'calendar_name': 'JSEEOM',
        'target_feature': 'Returns',
        'datasource_interpreter': 'StockDataSourceInterpreter',
        'prediction_result_interpreter': 'app.interpreters.prediction.metacrocubot_prediction_interpreter',
        'upload_strategy': 'OnDemandPredictionStrategy',
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
                'resume_training': False,
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

    def create_app(self):
        return APP

    def setUp(self):
        self.DB.drop_all()
        self.DB.create_all()

    def tearDown(self):
        from app.entities.datasource import DataSourceEntity
        uploads = [datasource.location for datasource in DataSourceEntity.query.all()]
        for upload in uploads:
            os.remove(upload)

        self.DB.session.remove()
        self.DB.drop_all()

    def create_superuser(self):
        create_admin(self.SUPERUSER_EMAIL, self.SUPERUSER_PASSWORD)

    def login_superuser(self):
        resp = self.client.post(
            url_for('authentication.login'),
            content_type='application/json',
            data=json.dumps({'email': self.SUPERUSER_EMAIL, 'password': self.SUPERUSER_PASSWORD}),
            headers={'Accept': 'application/json'}
        )
        assert resp.status_code == 200
        self.token = resp.json['token']

    def register_company(self):
        resp = self.client.post(
            url_for('company.register'),
            content_type='application/json',
            data=json.dumps(
                {'name': 'ACME Inc',
                 'domain': 'email.com'}
            )
        )
        assert resp.status_code == 201

    def set_company_configuration(self):
        resp = self.client.post(
            url_for('company.configuration_update', company_id=2),  # company 1 is the super-company...
            data=json.dumps(self.COMPANY_CONFIGURATION),
            content_type='application/json',
            headers={'Accept': 'application/json'}
        )

        assert resp.status_code == 201

    def register_user(self):
        # we won't accept a registration for a user not in the company...
        resp = self.client.post(
            url_for('user.register'),
            content_type='application/json',
            data=json.dumps({
                'email': 'test_user@email.co.uk',
                'password': 'password'
            })
        )

        assert resp.status_code == 400

        resp = self.client.post(
            url_for('user.register'),
            content_type='application/json',
            data=json.dumps({
                'email': self.USER_EMAIL,
                'password': self.USER_PASSWORD
            })
        )
        assert resp.status_code == 201
        confirmation_token = generate_confirmation_token('test_user@email.com')

        # we won't accept a login for a unconfirmed user...
        resp = self.client.post(
            url_for('authentication.login'),
            content_type='application/json',
            data=json.dumps({'email': self.USER_EMAIL, 'password': self.USER_PASSWORD})
        )
        assert resp.status_code == 401

        # we now require a confirmation for the user
        resp = self.client.get(
            url_for('user.confirm', token=confirmation_token)
        )
        assert resp.status_code == 200

    def login(self):
        # we now require a token authorization for the endpoints
        resp = self.client.post(
            url_for('authentication.login'),
            content_type='application/json',
            data=json.dumps({'email': self.USER_EMAIL, 'password': self.USER_PASSWORD}),
            headers={'Accept': 'application/json'}
        )

        assert resp.status_code == 200

        self.token = resp.json['token']

    def logout(self):
        resp = self.client.get(
            url_for('authentication.logout')
        )
        assert resp.status_code == 200
