from datetime import datetime

from flask import Blueprint, render_template

__all__ = ["index"]

home_bp = Blueprint("home", __name__, url_prefix="/")


@home_bp.route("/")
def index() -> str:
    return render_template(
        "homepage/home.html",
        now=datetime.utcnow(),
        view_name="homepage",
    )
