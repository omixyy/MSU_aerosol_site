from datetime import datetime

from flask import render_template
from flask.views import MethodView
from flask_login import current_user

from msu_aerosol.admin import get_complexes_dict

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

        complex_to_graphs = get_complexes_dict()
        return render_template(
            'contacts/developers.html',
            now=datetime.now(),
            view_name='developers_contacts',
            complex_to_graphs=complex_to_graphs,
            user=current_user,
        )


class ACContacts(MethodView):
    """
    Представление страницы "Контакты".
    """

    def get(self):
        complex_to_graphs = get_complexes_dict()
        return render_template(
            'contacts/ac_contacts.html',
            now=datetime.now(),
            view_name='ac_contacts',
            complex_to_graphs=complex_to_graphs,
            user=current_user,
        )
