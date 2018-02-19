import json

from flask import url_for

from test.functional.base_test_class import BaseTestClass


class TestContentNegotiation(BaseTestClass):

    def setUp(self):
        super(TestContentNegotiation, self).setUp()
        self.register_company()
        self.register_user()

    def test_login_can_deal_with_json(self):
        # json request
        resp = self.client.post(
            '/auth/login',
            content_type='application/json',
            data=json.dumps({'email': 'test_user@email.com', 'password': 'password'})
        )

        assert resp.content_type == 'application/json'
        assert not resp.headers.get('Location')
        assert 'token' in resp.json
        assert resp.status_code == 200

    def test_login_can_negotiate(self):
        resp = self.client.post(
            '/auth/login',
            content_type='application/json',
            data=json.dumps({'email': 'test_user@email.com', 'password': 'password'}),
            headers={'Accept': 'application/html'}

        )

        assert resp.headers.get('Location') == url_for('customer.dashboard', _external=True)

        resp = self.client.get(
            '/auth/logout',
            content_type='application/json',  # TODO: changeme!
            headers={'Accept': 'application/html'}
        )

        assert resp.headers.get('Location') == url_for('main.home', _external=True)
