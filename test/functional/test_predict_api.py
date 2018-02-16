import json
import os
import time

from flask_testing import TestCase

from app.db import db
from test.test_app import APP

HERE = os.path.join(os.path.dirname(__file__))


class TestPredictionAPI(TestCase):
    TESTING = True
    TEST_CUSTOMER_ID = '99'

    def create_app(self):
        return APP

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def register(self):
        resp = self.client.post(
            '/auth/register',
            content_type='application/json',
            data=json.dumps({
                'username': 'test_user',
                'password': 'password'
            })
        )
        assert resp.status_code == 201

    def login(self):
        self.register()
        # we now require a token authorization for the endpoints
        resp = self.client.post(
            '/auth/login',
            content_type='application/json',
            data=json.dumps({'username': 'test_user', 'password': 'password'})
        )

        assert resp.status_code == 303  # in order to redirect to the login page

        self.token = resp.json['token']

    def test_upload_file_for_customer(self):
        self.login()
        with open(os.path.join(HERE, '../resources/test_data.csv'), 'rb') as test_upload_file:
            resp = self.client.post(
                '/upload',
                content_type='multipart/form-data',
                data={'upload': (test_upload_file, 'test_data.csv')},
                #headers={'Authorization': self.token}
            )
            assert resp.status_code == 303  # in order to redirect to the dashboard
            assert resp.json

            """
            Response looks like:
            {
                'created_at': 'Wed, 07 Feb 2018 15:02:39 GMT', 
                'customer_id': '99', 
                'id': 1, 
                'last_update': 'Wed, 07 Feb 2018 15:02:39 GMT', 
                'location': '/Users/gabalese/projects/service-prediction-api/uploads/a033d3ae-cd6c-4435-b00b-0bbc9ab09fe6_test_data.csv', 
                'type': 'FILESYSTEM', 
                'upload_code': 'a033d3ae-cd6c-4435-b00b-0bbc9ab09fe6'
            }
            """
            assert resp.json['customer_id'] == 1

            assert resp.json['start_date'] == '2015-08-15T00:00:11'
            assert resp.json['end_date'] == '2015-08-15T03:21:14'

        with open(os.path.join(HERE, '../resources/additional_test_data.csv'), 'rb') as updated_data_file:
            resp = self.client.post(
                '/upload',
                content_type='multipart/form-data',
                data={'upload': (updated_data_file, 'test_data.csv')},
                # headers={'Authorization': self.token}
            )
            assert resp.status_code == 303  # in order to redirect to the dashboard
            assert resp.json
            assert resp.json['start_date'] == '2015-08-15T00:00:11'
            assert resp.json['end_date'] == '2017-08-15T03:21:14'

    def test_predict_on_a_file(self):
        self.login()
        # first you upload a file
        with open(os.path.join(HERE, '../resources/test_full_data.csv'), 'rb') as test_upload_file:
            resp = self.client.post(
                f'/upload',
                content_type='multipart/form-data',
                data={'upload': (test_upload_file, 'test_full_data.csv')},
                #headers={'Authorization': self.token}
            )

            upload_code = resp.json['upload_code']
            file_location = resp.json['location']
            assert upload_code
            assert file_location

        resp = self.client.post(
            '/predict/',
            content_type='application/json',
            data=json.dumps({
                "name": "TESTPREDICTION",
                "features": "number_people",
                "start_time": "2017-01-01T00:00:00",
                "end_time": "2017-01-02T00:00:00"}),
            headers={'Authorization': self.token}
        )
        assert resp.status_code == 303

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
            f'/predict/status/{task_code}',
            #headers={'Authorization': self.token}
        )
        """
        {
            'created_at': 'Wed, 07 Feb 2018 16:00:20 GMT', 
            'customer_id': 99, 
            'id': 1, 
            'last_update': 'Wed, 07 Feb 2018 16:00:20 GMT', 
            'status': 'QUEUED', 
            'task_code': 'd52c04e4-efdb-4c55-8c02-e8cf02f13a3c'
        }
        """
        assert resp.status_code == 200
        assert resp.json['customer_id'] == 1

        task_status = resp.json['status']

        while task_status not in ['SUCCESSFUL', 'FAILED']:
            time.sleep(2)
            resp = self.client.get(
                f'/predict/status/{task_code}',
                # headers={'Authorization': self.token}
            )
            task_status = resp.json['status']

        # check the result
        resp = self.client.get(
            f'/predict/result/{task_code}',
            #headers={'Authorization': self.token}
        )

        """
        {
            "customer_id": "99",
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
        assert resp.json['customer_id'] == 1
        assert resp.json['result']
        os.unlink(file_location)
