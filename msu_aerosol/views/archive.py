from datetime import datetime
from io import BytesIO
import os
from pathlib import Path
from zipfile import ZipFile

from flask import Blueprint, render_template, request, send_file
from flask_login import current_user

from msu_aerosol.admin import get_complexes_dict
from msu_aerosol.models import Complex, Device

__all__: list = []

archive_bp: Blueprint = Blueprint('about', __name__, url_prefix='/')


@archive_bp.route('/archive', methods=['GET'])
def archive() -> str:
    complex_to_device: dict[Complex, list[Device]] = get_complexes_dict()
    return render_template(
        'archive/archive.html',
        now=datetime.now(),
        view_name='archive',
        complex_to_device=complex_to_device,
        user=current_user,
    )


@archive_bp.route('/archive/<int:device_id>', methods=['GET', 'POST'])
def get_device_from_archive(device_id: int) -> str:
    device: Device = Device.query.get_or_404(device_id)
    complex_to_device: dict[Complex, list[Device]] = get_complexes_dict()
    path = f'data/{device.full_name}'
    files = os.listdir(path)
    if request.method == 'POST' and request.form['button'] == 'download':
        memory_file = BytesIO()
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

    return render_template(
        'archive/device_archive.html',
        now=datetime.now(),
        view_name='device_archive',
        device=device,
        user=current_user,
        complex_to_device=complex_to_device,
        files=files,
    )
