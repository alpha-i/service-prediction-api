import datetime
import json
import logging
import os
import time

from flask import url_for

from app import services, interpreters
from app.db import db
from app.interpreters.prediction import metacrocubot_prediction_interpreter
from test.functional.base_test_class import BaseTestClass

HERE = os.path.join(os.path.dirname(__file__))


class TestPredictionAPI(BaseTestClass):
    TESTING = True
    DB = db

    def setUp(self):
        super().setUp()
        self.create_superuser()
        self.login_superuser()
        self.register_company()
        self.register_user()
        self.set_company_configuration()
        self.logout()

    def test_predict_on_a_file(self):
        self.login()

        # first you upload a file
        with open(os.path.join(HERE, '../resources/test_stock_standardised.csv'), 'rb') as test_upload_file:
            resp = self.client.post(
                url_for('datasource.upload'),
                content_type='multipart/form-data',
                data={'upload': (test_upload_file, 'test_stock_standardised.csv')},
            )

            assert resp.status_code == 201
            upload_code = resp.json['upload_code']
            assert upload_code

        resp = self.client.post(
            url_for('prediction.submit'),
            content_type='application/json',
            data=json.dumps({
                "name": "TESTPREDICTION",
                "start_time": "2017-09-29T00:00:00",  # has to be the last date in the source
                "end_time": "2017-01-02T00:00:00"}  # is ignored by the metacrocubot
            ),
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
        )
        """
        {
            'created_at': 'Wed, 07 Feb 2018 16:00:20 GMT', 
            'company_id': 99, 
            'id': 1, 
            'last_update': 'Wed, 07 Feb 2018 16:00:20 GMT', 
            'status': 'QUEUED', 
            'task_code': 'd52c04e4-efdb-4c55-8c02-e8cf02f13a3c'
        }
        """
        assert resp.status_code == 200
        assert resp.json['company_id'] == 2

        task_status = resp.json['status']

        while task_status not in ['SUCCESSFUL', 'FAILED']:
            time.sleep(2)
            resp = self.client.get(
                url_for('prediction.get_single_task', task_code=task_code),
            )
            task_status = resp.json['status']

        resp = self.client.get(
            url_for('prediction.get_single_task', task_code=task_code),
        )

        assert len(resp.json['statuses']) == 5  # must have queued, started, 2 in progress, and successful

        # check the result
        resp = self.client.get(
            url_for('prediction.result', task_code=task_code),
        )

        """
        {
            "company_id": "99",
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
        assert resp.json['company_id'] == 2
        assert resp.json['result']

    def test_predict_no_task(self):
        self.login()
        with open(os.path.join(HERE, '../resources/test_stock_standardised.csv'), 'rb') as test_upload_file:
            resp = self.client.post(
                url_for('datasource.upload'),
                content_type='multipart/form-data',
                data={'upload': (test_upload_file, 'test_stock_standardised.csv')},
            )

            assert resp.status_code == 201
            upload_code = resp.json['upload_code']
            company_id = resp.json['company_id']
            assert upload_code
        self.logout()

        company_configuration = services.company.get_configuration_for_company_id(company_id)

        datasource = services.datasource.get_by_upload_code(upload_code)
        dataframe = services.datasource.get_dataframe(datasource)

        data_dict = interpreters.datasource.StockDataSourceInterpreter().from_dataframe_to_data_dict(dataframe)

        oracle = services.oracle.get_oracle_for_configuration(company_configuration)

        services.oracle.train(
            oracle=oracle,
            prediction_request={
                "name": "TEST_PREDICTION",
                "start_time": datetime.datetime(2017, 9, 29, 0, 0),
                "end_time": datetime.datetime(2017, 10, 29, 0, 0)  # is ignored anyway, so...
            },
            data_dict=data_dict
        )

        prediction = services.oracle.predict(
            oracle=oracle,
            prediction_request={
                "name": "TEST_PREDICTION",
                "start_time": datetime.datetime(2017, 9, 29, 0, 0),
                "end_time": datetime.datetime(2017, 10, 29, 0, 0)  # is ignored anyway, so...
            },
            data_dict=data_dict
        )

        interpreted_prediction = metacrocubot_prediction_interpreter(prediction)
