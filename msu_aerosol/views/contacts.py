from datetime import datetime

from flask import render_template
from flask.views import MethodView
from flask_login import current_user

from msu_aerosol.admin import get_complexes_dict, get_unique_devices

__all__: list = []


class DevelopersContacts(MethodView):
    """
    Представление страницы "Контакты разработчиков".
    """

    def get(self) -> str:
        """
        Метод GET для страницы, только он доступен.

        :return: Шаблон страницы "Контакты разработчиков"
        """

        complex_to_device = get_complexes_dict()
        return render_template(
            'contacts/developers.html',
            now=datetime.now(),
            view_name='developers_contacts',
            complex_to_device=complex_to_device,
            user=current_user,
            unique=get_unique_devices(),
        )


class ACContacts(MethodView):
    """
    Представление страницы "Контакты".
    """

    def get(self):
        complex_to_device = get_complexes_dict()
        return render_template(
            'contacts/ac_contacts.html',
            now=datetime.now(),
            view_name='ac_contacts',
            complex_to_device=complex_to_device,
            user=current_user,
            unique=get_unique_devices(),
        )
