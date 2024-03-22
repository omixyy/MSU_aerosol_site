from datetime import datetime

from flask import Blueprint, render_template

from msu_aerosol.models import Complex, Device
from msu_aerosol.admin import get_complexes_dict

__all__: list = []

home_bp: Blueprint = Blueprint("home", __name__, url_prefix="/")


@home_bp.route("/")
def index() -> str:
    complex_to_device: dict[Complex, list[Device]] = get_complexes_dict()
    return render_template(
        "homepage/home.html",
        now=datetime.now(),
        view_name="homepage",
        complex_to_device=complex_to_device,
    )
