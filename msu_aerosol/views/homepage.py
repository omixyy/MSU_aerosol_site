from datetime import datetime

from flask import render_template, request
from flask.views import MethodView
from flask_login import current_user

from msu_aerosol.admin import get_complexes_dict

__all__: list = []


class Home(MethodView):
    """
    Представление главной страницы.
    """

    def get(self) -> str:
        """
        Метод GET для страницы, только он доступен.

        :return: Шаблон главной страницы
        """

        complex_to_device = get_complexes_dict()
        return render_template(
            'home/homepage.html',
            now=datetime.now(),
            view_name='homepage',
            complex_to_device=complex_to_device,
            user=current_user,
        )
