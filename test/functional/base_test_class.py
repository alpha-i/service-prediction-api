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

    def get_company_configuration(self):
        configuration = {
            # this is the company_configuration.configuration
            "oracle_class": "alphai_crocubot_oracle.oracle.CrocubotOracle",
            "calendar_name": "GYMUK",
            "target_feature": "number_people",
            "datasource_interpreter": "GymDataSourceInterpreter",
            "prediction_result_interpreter": "",
            "oracle": {
                "universe": {
                    "method": "liquidity",
                    "n_assets": 10,
                    "ndays_window": 10,
                    "update_frequency": "weekly",
                    "avg_function": "median",
                    "dropna": False
                },
                "prediction_horizon": {
                    "unit": "days",
                    "value": 1,
                },
                "prediction_delta": {
                    "unit": "days",
                    "value": 10,
                },
                "training_delta": {
                    "unit": "days",
                    "value": 20,
                },
                "data_transformation": {
                    "fill_limit": 5,
                    "feature_config_list": [
                        {
                            "name": "number_people",
                            "normalization": "standard",
                            "length": 50,
                            "is_target": True
                        },
                    ],
                    "target_config_list": [
                        {
                            "name": "number_people",
                            "length": 5
                        },
                    ],
                    "features_ndays": 10,
                    "features_resample_minutes": 15,
                    "target_delta_ndays": 1,
                },
                "model": {
                    "train_path": "/tmp/crocubot",
                    "tensorboard_log_path": "/tmp/crocubot",
                    "covariance_method": "Ledoit",
                    "covariance_ndays": 100,
                    "model_save_path": "/tmp/crocubot",
                    "n_training_samples": 15800,
                    "INITIAL_ALPHA": 0.05,
                    "n_training_samples_benchmark": 1000,
                    "n_assets ": 10,
                    "classify_per_series ": False,
                    "normalise_per_series ": True,
                    "use_historical_covariance ": True,
                    "n_correlated_series ": 1,
                    "d_type": "float32",
                    "tf_type": 32,
                    "random_seed": 0,
                    "predict_single_shares": False,
                    "classify_per_series": True,
                    "normalise_per_series": True,

                    # Training specific
                    "n_epochs": 1,
                    "n_retrain_epochs": 1,
                    "learning_rate": 2e-3,
                    "batch_size": 100,
                    "cost_type": "bayes",
                    "n_train_passes": 32,
                    "n_eval_passes": 32,
                    "resume_training": False,
                    "use_gpu": False,  # my macbook doesn"t have a GPU :(((

                    # Topology
                    "n_series": 1,
                    "n_assets": 1,
                    "do_kernel_regularisation": True,
                    "do_batch_norm": False,
                    "n_res_blocks": 6,
                    "n_features_per_series": 271,
                    "n_forecasts": 5,  # WE HAVE TO CHANGE THIS
                    "n_classification_bins": 12,
                    "layer_heights": [400, 400, 400, 400],
                    "layer_widths": [1, 1, 1, 1],
                    "layer_types": ["conv", "res", "full", "full"],
                    "activation_functions": ["relu", "relu", "relu", "relu"],

                    # Initial conditions
                    "INITIAL_WEIGHT_UNCERTAINTY": 0.02,
                    "INITIAL_BIAS_UNCERTAINTY": 0.02,
                    "INITIAL_WEIGHT_DISPLACEMENT": 0.1,
                    "INITIAL_BIAS_DISPLACEMENT": 0.1,
                    "USE_PERFECT_NOISE": False,

                    # Priors
                    "double_gaussian_weights_prior": True,
                    "wide_prior_std": 1.0,
                    "narrow_prior_std": 0.001,
                    "spike_slab_weighting": 0.6
                }
            },
            "scheduling": {
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

    def set_company_configuration(self):
        configuration = self.get_company_configuration()
        resp = self.client.post(
            url_for('company.configuration_update', company_id=2),  # company 1 is the super-company...
            data=json.dumps(configuration),
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
