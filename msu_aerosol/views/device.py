from datetime import datetime

from flask import Blueprint, render_template
from flask_login import current_user

from msu_aerosol.admin import get_complexes_dict
from msu_aerosol.graph_funcs import choose_range, disk
from msu_aerosol.models import Complex, Device

__all__: list = []

device_bp: Blueprint = Blueprint("device", __name__, url_prefix="/")


@device_bp.route("/devices/<int:device_id>", methods=["GET", "POST"])
def device(device_id: int) -> str:
    device_orm_obj: Device = Device.query.get_or_404(device_id)
    complex_orm_obj: Complex = Complex.query.get(device_orm_obj.complex_id)
    complex_to_device: dict[Complex, list[Device]] = get_complexes_dict()
    device_to_name: dict[str, str] = {
        dev.name: disk.get_public_meta(dev.link)["name"]
        for dev in Device.query.all()
    }
    min_date, max_date = choose_range(device_to_name[device_orm_obj.name])
    return render_template(
        "device/device.html",
        now=datetime.now(),
        view_name="device",
        device=device_orm_obj,
        complex=complex_orm_obj,
        complex_to_device=complex_to_device,
        user=current_user,
        device_to_name=device_to_name,
        min_date=str(min_date).replace(" ", "T"),
        max_date=str(max_date).replace(" ", "T"),
    )
