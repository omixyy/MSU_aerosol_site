from datetime import datetime

from flask import Blueprint, render_template

from msu_aerosol import models

__all__ = ["index"]

home_bp: Blueprint = Blueprint("home", __name__, url_prefix="/")


@home_bp.route("/")
def index() -> str:
    all_devices: list[models.Device] = models.Device.query.all()
    return render_template(
        "homepage/home.html",
        now=datetime.now(),
        view_name="homepage",
        devices=all_devices,
    )
