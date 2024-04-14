from http import HTTPStatus
import unittest

from flask import request, url_for

from app import app

__all__: list = []


class TestStaticURL(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def test_url(self):
        with self.app.app_context(), self.app.test_request_context():
            response = self.client.get(url_for('home.index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_login(self):
        with self.app.app_context(), self.app.test_request_context():
            response = self.client.get(url_for('login.login'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_registration(self):
        with self.app.app_context(), self.app.test_request_context():
            response = self.client.get(url_for('registration.register'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile_unauthorized(self):
        with self.app.app_context(), self.app.test_request_context():
            response = self.client.get(url_for('profile.user_profile'))
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

    def test_authorization(self):
        with self.app.app_context(), self.app.test_request_context():
            response = self.client.post(
                url_for('registration.register'),
                data={
                    'login': 'TestLogin',
                    'email': 'test@email.com',
                    'password': 'TestPassword1221',
                    'password_again': 'TestPassword1221',
                },
                follow_redirects=True,
            )
            self.assertEqual(request.path, url_for('home.index'))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        with self.app.app_context(), self.app.test_request_context():
            response = self.client.get(url_for('profile.user_profile'))

        self.assertEqual(response.status_code, HTTPStatus.OK)
