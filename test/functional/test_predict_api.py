import json
import os
import time

import pytest
from flask import url_for

from test.functional.base_test_class import BaseTestClass

HERE = os.path.join(os.path.dirname(__file__))


class TestPredictionAPI(BaseTestClass):
    TESTING = True

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
                data={'upload': (updated_data_file, 'test_data.csv')},
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
            content_type='application/json',
            headers={'Accept': 'application/html'}
        )

        assert resp.status_code == 400

        # but they can delete updates
        resp = self.client.post(
            url_for('datasource.delete', datasource_id=second_upload_code),
            content_type='application/json',
            headers={'Accept': 'application/html'}
        )

        assert resp.status_code == 302

    @pytest.mark.skip('Waiting for the oracle to be fixed...')
    def test_predict_on_a_file(self):
        self.login()

        # first you upload a file
        with open(os.path.join(HERE, '../resources/test_full_data.csv'), 'rb') as test_upload_file:
            resp = self.client.post(
                url_for('datasource.upload'),
                content_type='multipart/form-data',
                data={'upload': (test_upload_file, 'test_full_data.csv')},
                headers={'Accept': 'application/html'}
            )

            upload_code = resp.json['upload_code']
            assert upload_code

        resp = self.client.post(
            url_for('prediction.submit'),
            content_type='application/json',
            data=json.dumps({
                "name": "TESTPREDICTION",
                "feature": "number_people",
                "start_time": "2017-01-01T00:00:00",
                "end_time": "2017-01-02T00:00:00"}),
            headers={'Authorization': self.token,
                     'Accept': 'application/html'}
        )
        assert resp.status_code == 302

        """
        Response looks like:
        {
            'result': 'http://localhost/predict/result/387c607d-6f4c-47f6-919a-87506ada7252', 
            'task_code': '387c607d-6f4c-47f6-919a-87506ada7252', 
            'task_status': 'http://localhost/predict/status/387c607d-6f4c-47f6-919a-87506ada7252'
        }
        """
        assert set(resp.json.keys()) == {'result', 'task_code', 'task_status'}

        task_code = resp.json['task_code']

        # you can query the task status
        time.sleep(4)
        resp = self.client.get(
            url_for('prediction.get_single_task', task_code=task_code)
            # headers={'Authorization': self.token}
        )
        """
        {
            'created_at': 'Wed, 07 Feb 2018 16:00:20 GMT', 
            'user_id': 99, 
            'id': 1, 
            'last_update': 'Wed, 07 Feb 2018 16:00:20 GMT', 
            'status': 'QUEUED', 
            'task_code': 'd52c04e4-efdb-4c55-8c02-e8cf02f13a3c'
        }
        """
        assert resp.status_code == 200
        assert resp.json['user_id'] == 2

        task_status = resp.json['status']

        while task_status not in ['SUCCESSFUL', 'FAILED']:
            time.sleep(2)
            resp = self.client.get(
                url_for('prediction.get_single_task', task_code=task_code),
                # headers={'Authorization': self.token}
            )
            task_status = resp.json['status']

        # check the result
        resp = self.client.get(
            url_for('prediction.result', task_code=task_code),
            # headers={'Authorization': self.token}
        )

        """
        {
            "user_id": "99",
            "result": [
                {
                    "prediction": [
                        {
                            "confidence": 0.40359007884378795,
                            "feature": "number_people",
                            "value": 1
                        }
                    ],
                    "timestamp": "2017-01-01"
                },
                {
                    "prediction": [
                        {
                            "confidence": 0.5873122611466733,
                            "feature": "number_people",
                            "value": 4
                        }
                    ],
                    "timestamp": "2017-01-02"
                }
            ],
            "task_code": "40f28db8-4ec8-499a-a337-34b25ea8b270"
        }
        """

        assert resp.status_code == 200
        assert resp.json['user_id'] == 2
        assert resp.json['result']
