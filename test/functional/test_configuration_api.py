import datetime

from flask import url_for, json

from test.functional.base_test_class import BaseTestClass


class TestConfigurationAPI(BaseTestClass):

    def setUp(self):
        super().setUp()
        self.register_company()
        self.register_user()
        self.login()

    def test_user_can_push_a_configuration(self):
        configuration = {
            "parameter_one": 1,
            "parameter_two": 2,
            "a_date": datetime.datetime(2018, 2, 20, 18, 39, 42)
        }
        resp = self.client.post(
            url_for('company.configuration_update'),
            data=json.dumps(configuration),
            content_type='application/json',
            headers={'Accept': 'application/json'}
        )

        assert resp.status_code == 201
        assert resp.json['a_date'] == '2018-02-20T18:39:42'
