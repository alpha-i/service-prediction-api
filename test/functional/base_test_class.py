import json
from flask_testing import TestCase

from app.core.auth import generate_confirmation_token
from app.db import db
from test.test_app import APP


class BaseTestClass(TestCase):
    TESTING = True
    USER_EMAIL = 'test_user@email.com'
    PASSWORD = 'password'

    def create_app(self):
        return APP

    def setUp(self):
        db.drop_all()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()


    def register_company(self):
        resp = self.client.post(
            '/auth/register-company',
            content_type='application/json',
            data=json.dumps(
                {'name': 'ACME Inc',
                 'domain': 'email.com'}
            )

        )
        assert resp.status_code == 201

    def register_user(self):

        # we won't accept a registration for a user not in the company...
        resp = self.client.post(
            '/auth/register-user',
            content_type='application/json',
            data=json.dumps({
                'email': 'test_user@email.co.uk',
                'password': 'password'
            })
        )

        assert resp.status_code == 401


        resp = self.client.post(
            '/auth/register-user',
            content_type='application/json',
            data=json.dumps({
                'email': self.USER_EMAIL,
                'password': self.PASSWORD
            })
        )
        assert resp.status_code == 201
        confirmation_token = generate_confirmation_token('test_user@email.com')

        # we won't accept a login for a unconfirmed user...
        resp = self.client.post(
            '/auth/login',
            content_type='application/json',
            data=json.dumps({'email': self.USER_EMAIL, 'password': self.PASSWORD})
        )
        assert resp.status_code == 401

        # we now require a confirmation for the user
        resp = self.client.get(
            f'/auth/confirm/{confirmation_token}'
        )
        assert resp.status_code == 200

    def login(self):
        # we now require a token authorization for the endpoints
        resp = self.client.post(
            '/auth/login',
            content_type='application/json',
            data=json.dumps({'email': self.USER_EMAIL, 'password': self.PASSWORD}),
            headers = {'Accept': 'application/json'}
        )

        assert resp.status_code == 200

        self.token = resp.json['token']

