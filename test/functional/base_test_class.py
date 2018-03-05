import json

from flask import url_for
from flask_testing import TestCase

from app.services.oracle import ORACLE_CONFIG
from app.services.user import generate_confirmation_token
from app.db import db
from test.test_app import APP


class BaseTestClass(TestCase):
    TESTING = True
    USER_EMAIL = 'test_user@email.com'
    PASSWORD = 'password'
    DB = db

    def create_app(self):
        return APP

    def setUp(self):
        self.DB.drop_all()
        self.DB.create_all()

    def tearDown(self):
        self.DB.session.remove()
        self.DB.drop_all()

    def register_company(self):
        resp = self.client.post(
            url_for('company.register'),
            content_type='application/json',
            data=json.dumps(
                {'name': 'ACME Inc',
                 'domain': 'email.com'}
            )

        )
        assert resp.status_code == 201

    def set_company_configuration(self):
        configuration = ORACLE_CONFIG
        configuration['oracle_class'] = 'alphai_cromulon_oracle.oracle.CromulonOracle'

        resp = self.client.post(
            url_for('company.configuration_update'),
            data=json.dumps(configuration),
            content_type='application/json',
            headers={'Accept': 'application/json'}
        )

        assert resp.status_code == 201

    def register_user(self):
        # we won't accept a registration for a user not in the company...
        resp = self.client.post(
            url_for('user.register'),
            content_type='application/json',
            data=json.dumps({
                'email': 'test_user@email.co.uk',
                'password': 'password'
            })
        )

        assert resp.status_code == 401

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

        # we won't accept a login for a unconfirmed user...
        resp = self.client.post(
            url_for('authentication.login'),
            content_type='application/json',
            data=json.dumps({'email': self.USER_EMAIL, 'password': self.PASSWORD})
        )
        assert resp.status_code == 401

        # we now require a confirmation for the user
        resp = self.client.get(
            url_for('user.confirm', token=confirmation_token)
        )
        assert resp.status_code == 200

    def login(self):
        # we now require a token authorization for the endpoints
        resp = self.client.post(
            url_for('authentication.login'),
            content_type='application/json',
            data=json.dumps({'email': self.USER_EMAIL, 'password': self.PASSWORD}),
            headers={'Accept': 'application/json'}
        )

        assert resp.status_code == 200

        self.token = resp.json['token']
