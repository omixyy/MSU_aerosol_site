from datetime import datetime
from io import BytesIO
import os
from pathlib import Path
from zipfile import ZipFile

from flask import abort, render_template, request, Response, send_file
from flask.views import MethodView
from flask_login import current_user, login_required

from msu_aerosol.admin import get_complexes_dict
from msu_aerosol.models import Complex, Device

__all__: list = []


class Archive(MethodView):
    """
    Представление страницы "Архив".
    """

    @login_required
    def get(self) -> str:
        """
        Метод GET для страницы архива, только он доступен.

        :return: Шаблон страницы "Архив"
        """

        if not (
            current_user
            and current_user.role
            and current_user.role.can_download_data
        ):
            abort(403)

        complex_to_graphs: dict = get_complexes_dict()
        complex_to_devices: dict = {
            com: Device.query.filter_by(complex_id=com.id)
            for com in Complex.query.all()
        }
        return render_template(
            'archive/archive.html',
            now=datetime.now(),
            view_name='archive',
            complex_to_graphs=complex_to_graphs,
            complex_to_devices=complex_to_devices,
            archived=Device.query.filter_by(archived=True),
            user=current_user,
        )


class DeviceArchive(MethodView):
    """
    Представление Страницы архива прибора.
    """

    @login_required
    def get(self, device_id: int) -> str:
        """
        Метод GET для страницы архива прибора.
        Получение все доступные на сервере файлы прибора,
        передача их в шаблон.

        :param device_id: Идентификатор прибора
        :return: Шаблон страницы архива прибора
        """

        if not current_user.role.can_download_data:
            abort(403)

        complex_to_graphs = get_complexes_dict()
        device = Device.query.get_or_404(device_id)
        path = f'data/{device.full_name}'
        listdir = os.listdir(path)
        delimiter = listdir[0][4]
        file = listdir[0]
        try:
            time_format = f'%Y{delimiter}%m{delimiter}%d'
            time_slice = slice(0, 10)
            datetime.strptime(file[time_slice], time_format)
        except ValueError:
            time_slice = slice(0, 7)
            time_format = f'%Y{delimiter}%m'
        files = sorted(
            listdir,
            key=lambda x: datetime.strptime(
                x[time_slice],
                time_format,
            ),
        )
        return render_template(
            'archive/device_archive.html',
            now=datetime.now(),
            view_name='device_archive',
            device=device,
            user=current_user,
            complex_to_graphs=complex_to_graphs,
            files=files,
        )

    @login_required
    def post(self, device_id: int) -> Response:
        """
        Метод POST для страницы архива прибора.
        Находит все доступные файлы прибора на сервере,
        отправляет их пользователю в виде zip-архива.

        :param device_id: Идентификатор прибора
        :return: zip-архив файлов прибора.
        """

        if not current_user.role.can_download_data:
            abort(403)

        device = Device.query.get_or_404(device_id)
        if request.form['button'] == 'download_all':
            memory_file = BytesIO()
            path = f'data/{device.full_name}'
            with ZipFile(memory_file, 'w') as zf:
                for root, dirs, files in os.walk(path):
                    for file in files:
                        file_path = Path(root) / file
                        zf.write(file_path, os.path.relpath(file_path, path))

            memory_file.seek(0)
            with Path('download_log.log', encoding='utf8').open('w') as log:
                log.write(
                    f'User {current_user.login} '
                    f'downloaded all files for {device.full_name}',
                )
            return send_file(
                memory_file,
                mimetype='application/zip',
                as_attachment=True,
                download_name='data.zip',
            )

        filename = request.form['button']
        with Path('download_log.log', encoding='utf8').open('w') as log:
            log.write(
                f'Пользователь {current_user.login} '
                f'скачал файл {filename} прибора {device.full_name} из архива',
            )
        return send_file(
            f'data/{device.full_name}/{filename}',
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename,
        )
