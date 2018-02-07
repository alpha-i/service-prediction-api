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

    def test_upload_file_for_customer(self):
        with open(os.path.join(HERE, '../resources/test_data.csv'), 'rb') as test_upload_file:
            resp = self.client.post(
                f'/upload/{self.TEST_CUSTOMER_ID}',
                content_type='multipart/form-data',
                data={'upload': (test_upload_file, 'test_data.csv')}
            )
            assert resp.status_code == 201
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
                'upload_id': 'a033d3ae-cd6c-4435-b00b-0bbc9ab09fe6'
            }
            """
            assert resp.json['customer_id'] == '99'
            file_location = resp.json['location']
            os.unlink(file_location)

    def test_predict_on_a_file(self):
        # first you upload a file
        with open(os.path.join(HERE, '../resources/test_data.csv'), 'rb') as test_upload_file:
            resp = self.client.post(
                f'/upload/{self.TEST_CUSTOMER_ID}',
                content_type='multipart/form-data',
                data={'upload': (test_upload_file, 'test_data.csv')}
            )

            upload_id = resp.json['upload_id']
            file_location = resp.json['location']

        resp = self.client.post(
            f'/predict/{self.TEST_CUSTOMER_ID}/{upload_id}',
            content_type='application/json',
            data=json.dumps({
                "features": ["number_people"],
                "start_time": "2017-01-01T00:00:00",
                "end_time": "2017-01-02T00:00:00"
            })
        )
        assert resp.status_code == 202

        """
        Response looks like:
        {
            'result': 'http://localhost/predict/result/387c607d-6f4c-47f6-919a-87506ada7252', 
            'task_id': '387c607d-6f4c-47f6-919a-87506ada7252', 
            'task_status': 'http://localhost/predict/status/387c607d-6f4c-47f6-919a-87506ada7252'
        }
        """
        assert set(resp.json.keys()) == {'result', 'task_id', 'task_status'}

        task_id = resp.json['task_id']

        # you can query the task status
        time.sleep(2)
        resp = self.client.get(f'/predict/status/{task_id}')
        """
        {
            'created_at': 'Wed, 07 Feb 2018 16:00:20 GMT', 
            'customer_id': 99, 
            'id': 1, 
            'last_update': 'Wed, 07 Feb 2018 16:00:20 GMT', 
            'status': 'QUEUED', 
            'task_id': 'd52c04e4-efdb-4c55-8c02-e8cf02f13a3c'
        }
        """
        assert resp.status_code == 200
        assert resp.json['customer_id'] == 99

        time.sleep(2)  # wait for the task to finish

        # check the result
        resp = self.client.get(f'/predict/result/{task_id}')

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
            "task_id": "40f28db8-4ec8-499a-a337-34b25ea8b270"
        }
        """

        assert resp.status_code == 200
        assert resp.json['customer_id'] == "99"  # TODO: why is this a string?
        assert len(resp.json['result']) == 2
        os.unlink(file_location)
