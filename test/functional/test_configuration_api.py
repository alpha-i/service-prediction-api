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
            "scheduling": {"something": "random"},
            "oracle": {"something": "else"},
            "oracle_class": "alphai_cromulon_oracle.oracle.CromulonOracle"
        }
        resp = self.client.post(
            url_for('company.configuration_update'),
            data=json.dumps(configuration),
            content_type='application/json',
            headers={'Accept': 'application/json'}
        )

        assert resp.status_code == 201
        assert resp.json == {
            'oracle': {'something': 'else'},
            'oracle_class': 'alphai_cromulon_oracle.oracle.CromulonOracle',
            'scheduling': {'something': 'random'}
        }
