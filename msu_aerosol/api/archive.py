from datetime import datetime
from io import BytesIO
import os
from pathlib import Path
from zipfile import ZipFile

from flask import make_response, render_template, send_file
from flask_login import current_user
from flask_restful import Resource

from msu_aerosol.admin import get_complexes_dict
from msu_aerosol.models import Complex, Device

__all__: list = []


class Archive(Resource):
    def get(self):
        complex_to_device: dict[Complex, list[Device]] = get_complexes_dict()
        return make_response(
            render_template(
                'archive/archive.html',
                now=datetime.now(),
                view_name='archive',
                complex_to_device=complex_to_device,
                user=current_user,
            ),
            200,
        )


class DeviceArchive(Resource):
    def get(self, device_id):
        complex_to_device: dict[Complex, list[Device]] = get_complexes_dict()
        device: Device = Device.query.get_or_404(device_id)
        path = f'data/{device.full_name}'
        files = os.listdir(path)
        return make_response(
            render_template(
                'archive/device_archive.html',
                now=datetime.now(),
                view_name='device_archive',
                device=device,
                user=current_user,
                complex_to_device=complex_to_device,
                files=files,
            ),
            200,
        )

    def post(self, device_id):
        memory_file = BytesIO()
        device: Device = Device.query.get_or_404(device_id)
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
