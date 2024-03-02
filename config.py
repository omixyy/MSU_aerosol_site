import os

BASEDIR = os.path.abspath(os.path.dirname(__file__))
STATIC_URL = BASEDIR + "/static_dev"


class Config(object):
    DEBUG = False
    CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = "dsofpkoasodksap"
    SECRET_KEY = "zxczxasdsad"
    SQLALCHEMY_DATABASE_URI = (
        "mysql+mysqlconnector://webuser:web_password@localhost/webuser_db",
    )


class ProductionConfig(Config):
    DEBUG = False


class DevelopConfig(Config):
    DEBUG = True
    ASSETS_DEBUG = True
