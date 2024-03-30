import unittest

from ..run import app

__all__ = []


class URLTests(unittest.TestCase):
    def create_app(self):
        app.config["TESTING"] = True
        return app

    def test_homepage_items(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Hello, World!", response.data)
