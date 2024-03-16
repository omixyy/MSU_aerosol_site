from datetime import datetime

from flask import Blueprint, render_template

__all__ = []

device_bp: Blueprint = Blueprint("device", __name__, url_prefix="/")


@device_bp.route("/device")
def device() -> str:
    return render_template(
        "device/device.html",
        now=datetime.now(),
        view_name="device",
    )
