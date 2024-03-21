from datetime import datetime

from flask import Blueprint, render_template

from msu_aerosol import models

__all__: list = []

home_bp: Blueprint = Blueprint("home", __name__, url_prefix="/")


@home_bp.route("/")
def index() -> str:
    all_complexes: list[models.Device] = models.Complex.query.all()
    complex_to_device: dict[models.Complex, models.Device] = {
        com: models.Device.query.filter(
            models.Device.complex_id == com.id,
        ).all()
        for com in all_complexes
    }
    return render_template(
        "homepage/home.html",
        now=datetime.now(),
        view_name="homepage",
        complex_to_device=complex_to_device,
    )
