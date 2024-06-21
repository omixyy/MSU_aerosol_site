from collections import Counter
from datetime import datetime
import json
from pathlib import Path

from flask import jsonify, render_template, request, Response
from flask.views import MethodView
from flask_login import current_user

from msu_aerosol.admin import get_complexes_dict

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
        complex_to_graphs: dict = {}
        if order:
            for key, value in complex_to_device_unsorted.items():
                order_list: list = order[: len(value)]
                graphs_list: list = []
                for i in order_list:
                    graph = list(
                        filter(
                            lambda x: x.id == int(i),
                            complex_to_device_unsorted[key],
                        ),
                    )

                    if graph:
                        graphs_list.append(graph[0])

                if len(complex_to_device_unsorted[key]) > len(graphs_list):
                    graphs_list.extend(
                        list(
                            (
                                Counter(complex_to_device_unsorted[key])
                                - Counter(graphs_list)
                            ).elements(),
                        ),
                    )

                complex_to_graphs[key] = graphs_list
                for _ in range(len(value)):
                    if order:
                        del order[0]
        else:
            complex_to_graphs = get_complexes_dict()
        return render_template(
            'home/homepage.html',
            now=datetime.now(),
            view_name='homepage',
            complex_to_graphs=complex_to_graphs,
            user=current_user,
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
