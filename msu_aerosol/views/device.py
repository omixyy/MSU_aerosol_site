from datetime import datetime

from flask import Blueprint, render_template
from flask_login import current_user

from msu_aerosol.admin import get_complexes_dict
from msu_aerosol.graph_funcs import disk
from msu_aerosol.models import Complex, Device

__all__: list = []

device_bp: Blueprint = Blueprint("device", __name__, url_prefix="/")


@device_bp.route("/devices/<int:device_id>")
def device(device_id: int) -> str:
    device: Device = Device.query.get_or_404(device_id)
    complex: Complex = Complex.query.get(device.complex_id)
    complex_to_device: dict[Complex, list[Device]] = get_complexes_dict()
    device_to_name: dict[Device, str] = {
        dev.name: disk.get_public_meta(dev.link)["name"]
        for dev in Device.query.all()
    }
    return render_template(
        "device/device.html",
        now=datetime.now(),
        view_name="device",
        device=device,
        complex=complex,
        complex_to_device=complex_to_device,
        user=current_user,
        device_to_name=device_to_name,
    )
