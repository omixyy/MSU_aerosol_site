import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask


basedir: Path = Path(os.path.dirname(__file__)).resolve().parent
load_dotenv()


class Config:
    SECRET_KEY: str | None = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI: str | None = os.getenv("DATABASE_URI")
    SESSION_COOKIE_NAME: str | None = os.getenv('SESSION_COOKIE_NAME')
    STATIC_FOLDER: Path = basedir / "static_dev"
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = True


class ProdConfig(Config):
    FLASK_ENV: str = "production"
    DEBUG: bool = False
    

class DevConfig(Config):
    FLASK_ENV: str = "development"
    DEBUG: bool = True


def initialize_flask_app(filename: str) -> Flask:
    app: Flask = Flask(
        filename,
        instance_relative_config=False,
        static_folder=Config.STATIC_FOLDER,
    )
    app.config.from_object(Config)
    return app
