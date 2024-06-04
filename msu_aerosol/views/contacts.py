from datetime import datetime

from flask import render_template
from flask.views import MethodView
from flask_login import current_user

from msu_aerosol.admin import get_complexes_dict

__all__: list = []


class Contacts(MethodView):
    def get(self) -> str:
        complex_to_device = get_complexes_dict()
        return render_template(
            'contacts/contacts.html',
            now=datetime.now(),
            view_name='contacts',
            complex_to_device=complex_to_device,
            user=current_user,
        )
