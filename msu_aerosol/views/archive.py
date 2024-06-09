from datetime import datetime
from io import BytesIO
import os
from pathlib import Path
from zipfile import ZipFile

from flask import render_template, Response, request, send_file
from flask.views import MethodView
from flask_login import current_user

from msu_aerosol.admin import get_complexes_dict
from msu_aerosol.models import Device

__all__: list = []


class Archive(MethodView):
    """
    Представление страницы "Архив".
    """

    def get(self) -> str:
        """
        Метод GET для страницы архива, только он доступен.

        :return: Шаблон страницы "Архив"
        """

        complex_to_device = get_complexes_dict()
        return render_template(
            'archive/archive.html',
            now=datetime.now(),
            view_name='archive',
            complex_to_device=complex_to_device,
            user=current_user,
        )


class DeviceArchive(MethodView):
    """
    Представление Страницы архива прибора.
    """

    def get(self, device_id: int) -> str:
        """
        Метод GET для страницы архива прибора.
        Получение все доступные на сервере файлы прибора,
        передача их в шаблон.

        :param device_id: Идентификатор прибора
        :return: Шаблон страницы архива прибора
        """

        complex_to_device = get_complexes_dict()
        device = Device.query.get_or_404(device_id)
        path = f'data/{device.full_name}'
        files = os.listdir(path)
        return render_template(
            'archive/device_archive.html',
            now=datetime.now(),
            view_name='device_archive',
            device=device,
            user=current_user,
            complex_to_device=complex_to_device,
            files=files,
        )

    def post(self, device_id: int) -> Response:
        """
        Метод POST для страницы архива прибора.
        Находит все доступные файлы прибора на сервере,
        отправляет их пользователю в виде zip-архива.

        :param device_id: Идентификатор прибора
        :return: zip-архив файлов прибора.
        """

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
            return send_file(
                memory_file,
                mimetype='application/zip',
                as_attachment=True,
                download_name='data.zip',
            )

        else:
            filename = request.form["button"]
            return send_file(
                f'data/{device}/{filename}',
                mimetype='text/csv',
                as_attachment=True,
                download_name=filename,
            )
