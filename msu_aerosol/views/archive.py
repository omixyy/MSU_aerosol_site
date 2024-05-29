from datetime import datetime
import os

from flask import Blueprint, render_template
from flask_login import current_user

from msu_aerosol.admin import get_complexes_dict
from msu_aerosol.models import Complex, Device

__all__: list = []

archive_bp: Blueprint = Blueprint('about', __name__, url_prefix='/')


@archive_bp.route('/archive', methods=['GET'])
def archive() -> str:
    complex_to_device: dict[Complex, list[Device]] = get_complexes_dict()
    return render_template(
        'archive/archive.html',
        now=datetime.now(),
        view_name='archive',
        complex_to_device=complex_to_device,
        user=current_user,
    )


@archive_bp.route('/archive/<int:device_id>', methods=['GET'])
def get_device_from_archive(device_id: int) -> str:
    device: Device = Device.query.get_or_404(device_id)
    complex_to_device: dict[Complex, list[Device]] = get_complexes_dict()
    files = os.listdir(f'data/{device.full_name}')
    return render_template(
        'archive/device_archive.html',
        now=datetime.now(),
        view_name='device_archive',
        device=device,
        user=current_user,
        complex_to_device=complex_to_device,
        files=files,
    )
