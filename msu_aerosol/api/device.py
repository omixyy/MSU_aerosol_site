from datetime import datetime
import logging
from pathlib import Path

from flask import (
    make_response,
    render_template,
    request,
    send_file,
)
from flask_login import current_user
from flask_restful import Resource
from werkzeug.utils import secure_filename

from msu_aerosol.admin import get_complexes_dict
from msu_aerosol.config import upload_folder
from msu_aerosol.graph_funcs import choose_range, preprocessing_one_file
from msu_aerosol.graph_funcs import make_graph
from msu_aerosol.models import Complex, Device

__all__: list = []


def get_device_template(device_id: int, **kwargs):
    message = kwargs.get('message')
    error = kwargs.get('error')
    device_orm_obj: Device = Device.query.get_or_404(device_id)
    complex_orm_obj: Complex = Complex.query.get(device_orm_obj.complex_id)
    complex_to_device: dict[Complex, list[Device]] = get_complexes_dict()
    device_to_name: dict[str, str] = {
        dev.name: dev.full_name for dev in Device.query.all()
    }
    min_date, max_date = choose_range(device_to_name[device_orm_obj.name])
    return make_response(
        render_template(
            'device/device.html',
            now=datetime.now(),
            view_name='device',
            device=device_orm_obj,
            complex=complex_orm_obj,
            complex_to_device=complex_to_device,
            user=current_user,
            device_to_name=device_to_name,
            min_date=str(min_date).replace(' ', 'T'),
            max_date=str(max_date).replace(' ', 'T'),
            message=message,
            error=error,
        ),
        200,
    )


class DevicePage(Resource):
    def get(self, device_id: int):
        return get_device_template(device_id)


class DeviceDownload(Resource):
    def post(self, device_id: int):
        data_range = (
            request.form.get('datetime_picker_start'),
            request.form.get('datetime_picker_end'),
        )
        full_name = Device.query.get(device_id).full_name
        buffer = make_graph(
            full_name,
            'download',
            begin_record_date=data_range[0],
            end_record_date=data_range[1],
        )
        logging.info(
            f'{current_user.login} downloaded '
            f'{full_name} data for '
            f'{[i.replace("T", " ") for i in data_range]} '
            f'period',
        )
        return send_file(
            buffer,
            as_attachment=True,
            attachment_filename=(
                f'{full_name}_{data_range[0]}-{data_range[1]}.csv'
            ),
            mimetype='text/csv',
        )


class DeviceUpload(Resource):
    def post(self, device_id: int):
        file = request.files['file']
        filename = secure_filename(file.filename)

        try:
            full_name = Device.query.get(device_id).full_name
            directory = Path(
                f'{upload_folder}/{full_name}',
            )
            if not directory.exists():
                Path(directory).mkdir(parents=True)
            file.save(
                Path(directory, filename),
            )
            preprocessing_one_file(
                full_name,
                Path(directory, filename),
                user_upload=True,
            )
            make_graph(full_name, 'full')
            make_graph(full_name, 'recent')
            return get_device_template(
                device_id,
                message='Файл успешно получен',
            )

        except Exception:
            return get_device_template(
                device_id,
                error='Ошибка при загрузке файла',
            )
