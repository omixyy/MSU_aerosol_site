from datetime import datetime

from flask import Blueprint, render_template
from flask_login import current_user

from msu_aerosol.admin import get_complexes_dict
from msu_aerosol.models import Complex, Device

__all__: list = []

about_bp: Blueprint = Blueprint('about', __name__, url_prefix='/')


@about_bp.route('/about', methods=['GET'])
def about() -> str:
    complex_to_device: dict[Complex, list[Device]] = get_complexes_dict()
    return render_template(
        'about/about.html',
        now=datetime.now(),
        view_name='about',
        complex_to_device=complex_to_device,
        user=current_user,
    )
