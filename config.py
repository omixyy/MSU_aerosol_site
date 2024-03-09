import os
from pathlib import Path
from dotenv import load_dotenv

__all__ = ["load_env_var"]


def load_env_var(value: str, default: bool) -> bool:
    env_value = os.getenv(value, str(default)).lower()
    return env_value in ("", "true", "yes", "1", "y")


load_dotenv()

BASEDIR = Path(os.path.dirname(__file__)).resolve()
STATIC_URL = BASEDIR / "static_dev"
DEBUG = load_env_var("DEBUG", "false")
