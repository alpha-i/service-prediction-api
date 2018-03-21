import os

import time
from flask import url_for

from app.entities import TaskStatusTypes
from test.functional.base_test_class import BaseTestClass

HERE = os.path.join(os.path.dirname(__file__))


class TestTriggerTrainingTask(BaseTestClass):
    TESTING = True

    def setUp(self):
        super().setUp()
        self.create_superuser()
        self.login_superuser()
        self.register_company()
        self.register_user()
        self.set_company_configuration()
        self.logout()

    def test_trigger_training_task(self):
        self.login()
        with open(os.path.join(HERE, '../resources/test_stock_standardised.csv'), 'rb') as test_upload_file:
            resp = self.client.post(
                url_for('datasource.upload'),
                content_type='multipart/form-data',
                data={'upload': (test_upload_file, 'test_stock_standardised.csv')},
            )
            assert resp.json


            upload_code = resp.json['upload_code']

        # a normal user can't trigger a train via the api
        resp = self.client.post(
            url_for('training.new', upload_code=upload_code)
        )

        assert resp.status_code == 403

        self.login_superuser()
        resp = self.client.post(
            url_for('training.new', upload_code=upload_code)
        )
        train_task_code = resp.json['task_code']

        self.logout()
        time.sleep(3)  # wait for task completion

        resp = self.client.get(
            url_for('training.detail', task_code=train_task_code)
        )

        assert resp.status_code == 200
        assert resp.json['status'] == TaskStatusTypes.successful.value
        assert len(resp.json['statuses']) == 2
