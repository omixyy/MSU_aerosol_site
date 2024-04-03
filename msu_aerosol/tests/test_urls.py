from http import HTTPStatus
import unittest

from flask import url_for

from main import app

__all__ = []


class TestStaticURLS(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

    def test_url(self):
        with app.app_context(), app.test_request_context():
            response = self.app.get(url_for("home.index"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_login(self):
        with app.app_context(), app.test_request_context():
            response = self.app.get(url_for("login.login"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_registration(self):
        with app.app_context(), app.test_request_context():
            response = self.app.get(url_for("registration.register"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
