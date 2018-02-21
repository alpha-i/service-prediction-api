import json

from flask import url_for

from app.core.auth import generate_confirmation_token
from test.functional.base_test_class import BaseTestClass


class TestContentNegotiation(BaseTestClass):

    def test_login_can_deal_with_json_as_default(self):
        self.register_company()
        self.register_user()
        # json request
        resp = self.client.post(
            url_for('authentication.login'),
            content_type='application/json',
            data=json.dumps({'email': self.USER_EMAIL, 'password': self.PASSWORD}),
            headers={'Accept': 'application/json'}
        )

        assert resp.content_type == 'application/json'
        assert not resp.headers.get('Location')
        assert 'token' in resp.json
        assert resp.status_code == 200

    def test_login_can_negotiate(self):
        self.register_company()
        self.register_user()
        resp = self.client.post(
            url_for('authentication.login'),
            content_type='application/json',
            data=json.dumps({'email': self.USER_EMAIL, 'password': self.PASSWORD}),
            headers={'Accept': 'application/html'}

        )

        assert resp.headers.get('Location') == url_for('customer.dashboard', _external=True)

        resp = self.client.get(
            url_for('authentication.logout'),
            content_type='application/json',  # TODO: changeme! it should accept html requests
            headers={'Accept': 'application/html'}
        )

        assert resp.headers.get('Location') == url_for('main.login', _external=True)

    def test_logout_can_negotiate(self):
        self.register_company()
        self.register_user()
        self.login()

        resp = self.client.get(url_for('authentication.logout'))

        assert resp.status_code == 200
        assert resp.headers.get('Set-Cookie') == 'token=; Expires=Thu, 01-Jan-1970 00:00:00 GMT; Path=/'

        self.login()

        resp = self.client.get(url_for('authentication.logout'), headers={'Accept': 'application/html'})

        assert resp.status_code == 302
        assert resp.headers.get('Location') == url_for('main.login', _external=True)

    def test_user_registration_can_render_json(self):
        self.register_company()

        resp = self.client.post(
            url_for('user.register'),
            content_type='application/json',
            headers={'Accept': 'application/json'},
            data=json.dumps({
                'email': self.USER_EMAIL,
                'password': self.PASSWORD
            })
        )

        assert resp.status_code == 201

    def test_user_registration_can_redirect(self):
        self.register_company()

        resp = self.client.post(
            url_for('user.register'),
            content_type='application/json',
            headers={'Accept': 'application/html'},
            data=json.dumps({
                'email': self.USER_EMAIL,
                'password': self.PASSWORD
            })
        )

        assert resp.status_code == 302

    def test_company_registration_can_negotiate(self):
        resp = self.client.post(
            url_for('company.register'),
            content_type='application/json',
            data=json.dumps(
                {'name': 'ACME Inc',
                 'domain': 'email.com'}
            )

        )
        assert resp.status_code == 201

        resp = self.client.post(
            url_for('company.register'),
            content_type='application/json',
            headers={'Accept': 'application/html'},
            data=json.dumps(
                {'name': 'ACME Inc',
                 'domain': 'email.it'}
            )
        )
        assert resp.status_code == 201

    def test_user_confirmation(self):
        self.register_company()

        # first register a user
        resp = self.client.post(
            url_for('user.register'),
            content_type='application/json',
            data=json.dumps({
                'email': self.USER_EMAIL,
                'password': self.PASSWORD
            })
        )
        assert resp.status_code == 201
        confirmation_token = generate_confirmation_token('test_user@email.com')

        resp = self.client.get(
            url_for('user.confirm', token=confirmation_token),
            headers={'Accept': 'application/html'}
        )
        assert resp.status_code == 302
        assert resp.headers.get('Location') == url_for('main.login', _external=True)
