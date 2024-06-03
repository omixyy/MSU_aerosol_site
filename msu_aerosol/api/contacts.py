from datetime import datetime

from flask import make_response, render_template, Response
from flask_login import current_user
from flask_restful import Resource

from msu_aerosol.admin import get_complexes_dict

__all__: list = []


class Contacts(Resource):
    def get(self) -> Response:
        complex_to_device = get_complexes_dict()
        return make_response(
            render_template(
                'contacts/contacts.html',
                now=datetime.now(),
                view_name='contacts',
                complex_to_device=complex_to_device,
                user=current_user,
            ),
            200,
        )
