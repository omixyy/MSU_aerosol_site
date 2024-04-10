import unittest

from flask import url_for
from flask_login import current_user
import parameterized

from app import app
from msu_aerosol.models import db

__all__: list = []


class TestRegisterForm(unittest.TestCase):
    def setUp(self) -> None:
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    @parameterized.parameterized.expand(
        [
            (
                {
                    "login": "TestLogin1",
                    "email": "test1@email.ru",
                    "password": "(@Q*DYqdw12)e23",
                    "password_again": "(@Q*DYqdw12)e23",
                },
            ),
            (
                {
                    "login": "TestLogin2",
                    "email": "test2@email.ru",
                    "password": "asddsgfew32",
                    "password_again": "asddsgfew32",
                },
            ),
            (
                {
                    "login": "TestLogin3",
                    "email": "test3@email.ru",
                    "password": "GEGW#Q@$GW",
                    "password_again": "GEGW#Q@$GW",
                },
            ),
        ],
    )
    def test_register_form_authenticated(self, data):
        with self.app.app_context(), self.app.test_request_context():
            self.client.post(
                url_for("registration.register"),
                data=data,
                follow_redirects=True,
            )

            self.assertTrue(current_user.is_authenticated)

    @parameterized.parameterized.expand(
        [
            (
                {
                    "login": "TestLogin1",
                    "email": "testl1@email.ru",
                    "password": "(@Q*DYqdq3werw12)e23",
                    "password_again": "(@Q*DYqdw12)e23",
                },
            ),
            (
                {
                    "login": "TestLogin2",
                    "email": "testl2@email.ru",
                    "password": "asddsgfew32",
                    "password_again": "asddsasfg4ggfew32",
                },
            ),
            (
                {
                    "login": "TestLogin3",
                    "email": "testl3@email.ru",
                    "password": "GEGW#Q@$GW",
                    "password_again": "GEGW#ase2w2@$GW",
                },
            ),
        ],
    )
    def test_register_form_not_authenticated(self, data):
        with self.app.app_context(), self.app.test_request_context():
            self.client.post(
                url_for("registration.register"),
                data=data,
                follow_redirects=True,
            )

            self.assertFalse(current_user.is_authenticated)


class TestLoginForm(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def test_auth(self):
        with self.app.app_context(), self.app.test_request_context():
            self.client.post(
                url_for("registration.register"),
                data={
                    "login": "TestLoginForm",
                    "email": "testlogin@email.ru",
                    "password": "_)@*(HF3-08fh)",
                    "password_again": "_)@*(HF3-08fh)",
                },
                follow_redirects=True,
            )
            self.assertTrue(current_user.is_authenticated)
