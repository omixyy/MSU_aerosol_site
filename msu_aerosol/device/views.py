from datetime import datetime

from flask import Blueprint, render_template

from msu_aerosol.models import Complex, Device
from msu_aerosol.admin import get_complexes_dict

__all__: list = []

device_bp: Blueprint = Blueprint("device", __name__, url_prefix="/")


@device_bp.route("/devices/<int:device_id>")
def device(device_id: int) -> str:
    device: Device = Device.query.get_or_404(device_id)
    complex: Complex = Complex.query.get(device.complex_id)
    complex_to_device: dict[Complex, list[Device]] = get_complexes_dict()
    return render_template(
        "device/device.html",
        now=datetime.now(),
        view_name="device",
        device=device,
        complex=complex,
        complex_to_device=complex_to_device,
    )
