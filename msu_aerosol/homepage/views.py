from datetime import datetime

from flask import Blueprint, render_template

__all__ = ["index"]

home_bp: Blueprint = Blueprint("home", __name__, url_prefix="/")


@home_bp.route("/")
def index() -> str:
    return render_template(
        "homepage/home.html",
        now=datetime.now(),
        view_name="homepage",
    )
