import os

from flask import url_for

from test.functional.base_test_class import BaseTestClass

HERE = os.path.join(os.path.dirname(__file__))


class TestDataSourceUpload(BaseTestClass):
    TESTING = True

    COMPANY_CONFIGURATION = {
        'oracle_class': 'test.mock_oracle.MockMetaCrocubot',
        'calendar_name': 'GYMUK',
        'target_feature': 'number_people',
        'datasource_interpreter': 'GymDataSourceInterpreter',
        'prediction_result_interpreter': 'app.interpreters.prediction.metacrocubot_prediction_interpreter',
        'oracle': {
            'universe': {
                'method': 'liquidity',
                'n_assets': 10,
                'ndays_window': 10,
                'update_frequency': 'weekly',
                'avg_function': 'median',
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
                'resume_training': True,
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
            'prediction_frequency': {
                'frequency_type': 'DAILY',
                'days_offset': 0,
                'minutes_offset': 15
            },
            'training_frequency': {
                'frequency_type': 'WEEKLY',
                'days_offset': 0,
                'minutes_offset': 15
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

    def test_upload_file_for_customer(self):
        self.login()
        with open(os.path.join(HERE, '../resources/test_data.csv'), 'rb') as test_upload_file:
            resp = self.client.post(
                url_for('datasource.upload'),
                content_type='multipart/form-data',
                data={'upload': (test_upload_file, 'test_data.csv')},
                headers={'Accept': 'application/html'}
            )
            assert resp.status_code == 302  # in order to redirect to the dashboard
            assert resp.json

            """
            Response looks like:
            {
                'created_at': 'Wed, 07 Feb 2018 15:02:39 GMT', 
                'user_id': '99', 
                'id': 1, 
                'last_update': 'Wed, 07 Feb 2018 15:02:39 GMT', 
                'location': '/Users/gabalese/projects/service-prediction-api/uploads/a033d3ae-cd6c-4435-b00b-0bbc9ab09fe6_test_data.csv', 
                'type': 'FILESYSTEM', 
                'upload_code': 'a033d3ae-cd6c-4435-b00b-0bbc9ab09fe6'
            }
            """
            assert resp.json['user_id'] == 2

            assert resp.json['start_date'] == '2015-08-15T00:00:11+00:00'
            assert resp.json['end_date'] == '2015-08-15T03:21:14+00:00'

        with open(os.path.join(HERE, '../resources/additional_test_data.csv'), 'rb') as updated_data_file:
            resp = self.client.post(
                url_for('datasource.upload'),
                content_type='multipart/form-data',
                data={'upload': (updated_data_file, 'additional_test_data.csv')},
                headers={'Accept': 'application/html'}
            )
            assert resp.status_code == 302  # in order to redirect to the dashboard
            assert resp.json
            assert resp.json['start_date'] == '2015-08-15T00:00:11+00:00'
            assert resp.json['end_date'] == '2017-08-15T03:21:14+00:00'

    def test_user_can_delete_a_datasource(self):
        self.login()
        with open(os.path.join(HERE, '../resources/test_data.csv'), 'rb') as test_upload_file:
            resp = self.client.post(
                url_for('datasource.upload'),
                content_type='multipart/form-data',
                data={'upload': (test_upload_file, 'test_data.csv')},
                headers={'Accept': 'application/html'}
            )
            assert resp.status_code == 302  # in order to redirect to the dashboard
            assert resp.json
            original_upload_code = resp.json['upload_code']

        with open(os.path.join(HERE, '../resources/test_data.csv'), 'rb') as test_upload_file:
            resp = self.client.post(
                url_for('datasource.upload'),
                content_type='multipart/form-data',
                data={'upload': (test_upload_file, 'test_data.csv')},
                headers={'Accept': 'application/html'}
            )
            assert resp.status_code == 302  # in order to redirect to the dashboard
            assert resp.json
            second_upload_code = resp.json['upload_code']

        # users can't delete the original data source
        resp = self.client.post(
            url_for('datasource.delete', datasource_id=original_upload_code),
            content_type='application/html',
            headers={'Accept': 'application/html'}
        )

        assert resp.status_code == 302

        # users can't delete the original data source
        resp = self.client.post(
            url_for('datasource.delete', datasource_id=original_upload_code),
            content_type='application/json',
            headers={'Accept': 'application/json'}
        )

        assert resp.status_code == 400

        # but they can delete updates
        resp = self.client.post(
            url_for('datasource.delete', datasource_id=second_upload_code),
            content_type='application/json',
            headers={'Accept': 'application/html'}
        )

        assert resp.status_code == 302
