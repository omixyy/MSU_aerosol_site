from datetime import datetime

from flask import Blueprint, render_template
from flask_login import current_user

from msu_aerosol.admin import get_complexes_dict
from msu_aerosol.models import Complex, Device

__all__: list = []

contacts_bp: Blueprint = Blueprint('about', __name__, url_prefix='/')


@contacts_bp.route('/contacts', methods=['GET'])
def contacts() -> str:
    complex_to_device: dict[Complex, list[Device]] = get_complexes_dict()
    return render_template(
        'contacts/contacts.html',
        now=datetime.now(),
        view_name='contacts',
        complex_to_device=complex_to_device,
        user=current_user,
    )