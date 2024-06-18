from collections import Counter
from datetime import datetime
import json
from pathlib import Path

from flask import jsonify, render_template, request, Response
from flask.views import MethodView
from flask_login import current_user

from msu_aerosol.admin import get_complexes_dict, get_unique_devices

__all__: list = []
ORDER_FILE = 'schema/block_order.json'


class BlockOrderHandler:
    """
    Обработчик файла с настройками главной страницы.
    """

    def __init__(self, filename):
        self.filename = filename

    def load_order(self) -> list:
        """
        Загрузка файла.

        :return: Загруженный json файл
        """
        try:
            with Path(self.filename).open('r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def save_order(self, order):
        with Path(self.filename).open('w') as f:
            json.dump(order, f)


class Home(MethodView):
    """
    Представление главной страницы.
    """

    def get(self) -> str:
        """
        Метод GET для страницы, только он доступен.

        :return: Шаблон главной страницы
        """

        order_handler = BlockOrderHandler('schema/block_order.json')
        order = order_handler.load_order()
        complex_to_device_unsorted = get_complexes_dict()
        complex_to_device: dict = {}
        if order:
            for key, value in complex_to_device_unsorted.items():
                order_list: list = order[: len(value)]
                devices_list: list = []
                for i in order_list:
                    device = list(
                        filter(
                            lambda x: x.id == int(i),
                            complex_to_device_unsorted[key],
                        ),
                    )

                    if device:
                        devices_list.append(device[0])

                if len(complex_to_device_unsorted[key]) > len(devices_list):
                    devices_list.extend(
                        list(
                            (
                                Counter(complex_to_device_unsorted[key])
                                - Counter(devices_list)
                            ).elements(),
                        ),
                    )

                complex_to_device[key] = devices_list
                for _ in range(len(value)):
                    if order:
                        del order[0]
        else:
            complex_to_device = get_complexes_dict()
        return render_template(
            'home/homepage.html',
            now=datetime.now(),
            view_name='homepage',
            complex_to_device=complex_to_device,
            user=current_user,
            unique=get_unique_devices(),
        )


class UpdateIndex(MethodView):
    """
    Класс, благодаря которому будет сохраняться порядок
    расположения приборов на главной странице.
    """

    def post(self) -> Response:
        """
        Метод POST, только он доступен.

        :return:
        """

        order_handler = BlockOrderHandler(ORDER_FILE)
        data = request.get_json()
        order = data.get('order')
        order_handler.save_order(order)
        return jsonify(success=True)
