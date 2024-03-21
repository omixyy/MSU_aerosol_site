from datetime import datetime

from flask import Blueprint, render_template

from msu_aerosol import models

__all__: list = []

device_bp: Blueprint = Blueprint("device", __name__, url_prefix="/")


@device_bp.route("/devices/<device_id>")
def device(device_id: int) -> str:
    device: models.Device = models.Device.query.get_or_404(device_id)
    complex: models.Complex = models.Complex.query.get(device.complex_id)
    return render_template(
        "device/device.html",
        now=datetime.now(),
        view_name="device",
        device=device,
        complex=complex,
    )
