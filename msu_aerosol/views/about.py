from datetime import datetime

from flask import render_template
from flask.views import MethodView
from flask_login import current_user

from msu_aerosol.admin import get_complexes_dict

__all__: list = []


class About(MethodView):
    """
    Представление страницы "О сайте".
    """

    def get(self) -> str:
        """
        Метод GET для страницы, только он доступен.

        :return: Шаблон страницы "О сайте"
        """

        complex_to_graphs = get_complexes_dict()
        return render_template(
            'about/about.html',
            now=datetime.now(),
            view_name='about',
            complex_to_graphs=complex_to_graphs,
            user=current_user,
        )
