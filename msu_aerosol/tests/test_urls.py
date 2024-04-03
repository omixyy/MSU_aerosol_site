import unittest
from main import app


class TestStaticURLS(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

    def test_homepage(self):
        response = self.app.get("/")
        self.assertEqual(response.status_code, 200)
