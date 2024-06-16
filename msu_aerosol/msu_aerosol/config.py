import os
from pathlib import Path
import uuid

from dotenv import load_dotenv
from flask import Flask

__all__: list = []

load_dotenv()
basedir = Path(os.path.dirname(__file__)).resolve().parent
yadisk_token = os.getenv('YADISK_TOKEN', default='FAKE_TOKEN')
upload_folder = 'received_data'
allowed_extensions = ['csv', 'xlsx']


class Config:
    SECRET_KEY = str(uuid.uuid4())
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'
    SESSION_COOKIE_NAME = os.getenv(
        'SESSION_COOKIE_NAME',
        default='FAKE_SESSION_COOKIE_NAME',
    )
    STATIC_FOLDER = basedir / 'static'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    TEMPLATES_AUTO_RELOAD = True


class ProdConfig(Config):
    FLASK_ENV = 'production'
    DEBUG = False


class DevConfig(Config):
    FLASK_ENV = 'development'
    DEBUG = True


def initialize_flask_app(filename: str) -> Flask:
    app = Flask(
        filename,
        instance_relative_config=False,
        static_folder=Config.STATIC_FOLDER,
    )
    app.config.from_object(ProdConfig)
    return app
