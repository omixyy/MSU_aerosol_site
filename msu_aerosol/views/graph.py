from datetime import datetime
import logging
from pathlib import Path

from flask import abort, redirect, url_for
from flask import (
    render_template,
    request,
    Response,
    send_file,
)
from flask.views import MethodView
from flask_login import current_user
from werkzeug.utils import secure_filename

from forms.file_form import FileForm
from msu_aerosol.admin import get_complexes_dict
from msu_aerosol.config import allowed_extensions, upload_folder
from msu_aerosol.exceptions import FileExtensionError
from msu_aerosol.graph_funcs import choose_range, preprocessing_one_file
from msu_aerosol.graph_funcs import make_graph
from msu_aerosol.models import Complex, Device, Graph

__all__: list = []


def get_device_template(graph_id: int, **kwargs) -> str:
    """
    Функция, возвращающая шаблон страницы прибора.
    Получает все необходимые переменные из kwargs и БД,
    передаём их в шаблон.

    :param graph_id: Идентификатор графика
    :param kwargs: Словарь с ключами 'message' и 'error'
    :return: Шаблон страницы прибора
    """

    message = kwargs.get('message')
    error = kwargs.get('error')
    form = kwargs.get('form')
    graph_orm_obj = Graph.query.get_or_404(graph_id)
    complex_orm_obj = Complex.query.get_or_404(graph_orm_obj.device.complex_id)
    complex_to_graphs = get_complexes_dict()
    device_to_name = {dev.name: dev.full_name for dev in Device.query.all()}
    min_date, max_date = choose_range(Graph.query.get(graph_id))
    return render_template(
        'device/device.html',
        now=datetime.now(),
        view_name='device',
        graph=graph_orm_obj,
        complex=complex_orm_obj,
        complex_to_graphs=complex_to_graphs,
        user=current_user,
        device_to_name=device_to_name,
        min_date=str(min_date).replace(' ', 'T'),
        max_date=str(max_date).replace(' ', 'T'),
        message=message,
        error=error,
        form=form,
    )


class GraphPage(MethodView):
    """
    Представление страницы прибора.
    """

    def get(self, graph_id: int) -> str:
        """
        Метод GET для страницы.

        :return: Шаблон страницы прибора
        """

        try:
            form = FileForm()
            return get_device_template(graph_id, form=form)

        except IndexError:
            abort(404)

    def post(self, graph_id: int) -> str | Response:
        """
        Метод POST для страницы.
        Пробует построить график для прибора с новым файлом,
        если не получается - сообщает об ошибке.

        :param graph_id: Идентификатор графика
        :return: Шаблон страницы прибора
        """

        form = FileForm()
        if form.validate_on_submit():
            file = form.file.data
            filename = secure_filename(form.file.data.filename)

            try:
                extension = filename.split('.')[-1]
                if extension not in allowed_extensions:
                    raise FileExtensionError
                name = Graph.query.get(graph_id).name
                directory = f'{upload_folder}/{name}'
                if not Path(directory).exists():
                    Path(directory).mkdir(parents=True)
                file.save(
                    Path(directory, filename),
                )
                graph = Graph.query.get(graph_id)
                preprocessing_one_file(
                    graph,
                    str(Path(directory) / filename),
                    user_upload=True,
                )
                make_graph(graph, 'full')
                make_graph(graph, 'recent')
                return get_device_template(
                    graph_id,
                    message='Файл успешно получен',
                    form=form,
                )

            except (Exception, FileExtensionError):
                return get_device_template(
                    graph_id,
                    error='Ошибка при загрузке файла',
                    form=form,
                )

        return redirect(url_for('home'))


class GraphDownload(MethodView):
    """
    Представление страницы скачивания файла прибора по выбранному диапазону.
    """

    def post(self, graph_id: int) -> Response:
        """
        Метод POST для страницы, только он доступен.
        Получат все данные, введённые пользователем,
        отправляет ему файл с данными по выбранному диапазону.

        :param graph_id: Идентификатор прибора
        :return: Файл с данными
        """

        data_range = (
            request.form.get('datetime_picker_start'),
            request.form.get('datetime_picker_end'),
        )
        graph = Graph.query.get(graph_id)
        buffer = make_graph(
            graph,
            'download',
            begin_record_date=data_range[0],
            end_record_date=data_range[1],
        )
        logging.info(
            f'{current_user.login} скачал данные прибора '
            f'{graph.device.name} по графику {graph.name} за период '
            f'{[i.replace("T", " ") for i in data_range]} '
            f'в {datetime.now()}',
        )
        return send_file(
            buffer,
            as_attachment=True,
            attachment_filename=(
                f'{graph.name}_{data_range[0]}-{data_range[1]}.csv'
            ),
            mimetype='text/csv',
        )
