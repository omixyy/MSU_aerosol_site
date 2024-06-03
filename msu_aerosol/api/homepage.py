from datetime import datetime

from flask import make_response, render_template
from flask_login import current_user
from flask_restful import Resource

from msu_aerosol.admin import get_complexes_dict
from msu_aerosol.models import Complex, Device

__all__: list = []


class Home(Resource):
    def get(self):
        complex_to_device: dict[Complex, list[Device]] = get_complexes_dict()
        return make_response(
            render_template(
                'home/homepage.html',
                now=datetime.now(),
                view_name='homepage',
                complex_to_device=complex_to_device,
                user=current_user,
            ),
            200,
        )
