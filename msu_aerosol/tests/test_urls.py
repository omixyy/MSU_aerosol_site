from http import HTTPStatus
import unittest

from flask import request, url_for

from main import app
from msu_aerosol.models import (
    Complex,
    db,
    Device,
)

__all__: list = []


class TestStaticURL(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        complex = Complex(
            name="TestComplex",
        )
        db.session.add(complex)
        db.session.commit()
        device = Device(
            name="TestDevice",
            link="https://disk.yandex.ru/d/3iruCwAKaGUD7g",
            complex_id=Complex.query.first().id,
        )
        db.session.add(device)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_url(self):
        with self.app.app_context(), self.app.test_request_context():
            response = self.client.get(url_for("home.index"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_login(self):
        with self.app.app_context(), self.app.test_request_context():
            response = self.client.get(url_for("login.login"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_registration(self):
        with self.app.app_context(), self.app.test_request_context():
            response = self.client.get(url_for("registration.register"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile_unauthorized(self):
        with self.app.app_context(), self.app.test_request_context():
            response = self.client.get(url_for("profile.user_profile"))
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

    def test_authorization(self):
        with self.app.app_context(), self.app.test_request_context():
            response = self.client.post(
                url_for("registration.register"),
                data={
                    "login": "TestLogin",
                    "email": "test@email.com",
                    "password": "TestPassword1221",
                    "password_again": "TestPassword1221",
                },
                follow_redirects=True,
            )
            self.assertEqual(request.path, url_for("home.index"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        with self.app.app_context(), self.app.test_request_context():
            response = self.client.get(url_for("profile.user_profile"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_send_settings_form(self):
        with self.app.app_context(), self.app.test_request_context():
            response = self.client.post(
                url_for("admin.index"),
                data={},
            )
