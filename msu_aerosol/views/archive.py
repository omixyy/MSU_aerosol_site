from datetime import datetime

from flask import Blueprint, render_template, request
from flask_login import current_user

from msu_aerosol.admin import get_complexes_dict
from msu_aerosol.models import Complex, Device

__all__: list = []

archive_bp: Blueprint = Blueprint('about', __name__, url_prefix='/')


@archive_bp.route('/archive', methods=['GET', 'POST'])
def archive() -> str:
    complex_to_device: dict[Complex, list[Device]] = get_complexes_dict()
    return render_template(
        'archive/archive.html',
        now=datetime.now(),
        view_name='archive',
        complex_to_device=complex_to_device,
        user=current_user,
    )
