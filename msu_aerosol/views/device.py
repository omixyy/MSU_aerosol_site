from datetime import datetime
from pathlib import Path

from flask import (
    Blueprint,
    render_template,
    request,
    Response,
    send_file,
)
from flask_login import current_user
from werkzeug.utils import secure_filename

from msu_aerosol.admin import get_complexes_dict
from msu_aerosol.config import allowed_extensions, upload_folder
from msu_aerosol.graph_funcs import choose_range, preprocessing_one_file
from msu_aerosol.graph_funcs import make_graph
from msu_aerosol.models import Complex, Device

__all__: list = []

device_bp: Blueprint = Blueprint("device", __name__, url_prefix="/")


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in allowed_extensions
    )


def get_device_template(device_id: int, **kwargs):
    message = kwargs["message"] if "message" in kwargs else None
    error = kwargs["error"] if "error" in kwargs else None
    device_orm_obj: Device = Device.query.get_or_404(device_id)
    complex_orm_obj: Complex = Complex.query.get(device_orm_obj.complex_id)
    complex_to_device: dict[Complex, list[Device]] = get_complexes_dict()
    device_to_name: dict[str, str] = {
        dev.name: dev.full_name for dev in Device.query.all()
    }
    min_date, max_date = choose_range(device_to_name[device_orm_obj.name])
    return render_template(
        "device/device.html",
        now=datetime.now(),
        view_name="device",
        device=device_orm_obj,
        complex=complex_orm_obj,
        complex_to_device=complex_to_device,
        user=current_user,
        device_to_name=device_to_name,
        min_date=str(min_date).replace(" ", "T"),
        max_date=str(max_date).replace(" ", "T"),
        message=message,
        error=error,
    )


@device_bp.route("/devices/<int:device_id>", methods=["GET", "POST"])
def device(device_id: int) -> str | Response:
    return get_device_template(device_id)


@device_bp.route(
    "/devices/<int:device_id>/download",
    methods=["GET", "POST"],
)
def download_data_range(device_id: int) -> Response:
    data_range = request.form.get(
        "datetime_picker_start",
    ), request.form.get("datetime_picker_end")
    full_name = Device.query.get(device_id).full_name
    buffer = make_graph(
        full_name,
        "download",
        begin_record_date=data_range[0],
        end_record_date=data_range[1],
    )
    return send_file(
        buffer,
        as_attachment=True,
        attachment_filename=f"{full_name}_{data_range[0]}-{data_range[1]}.csv",
        mimetype="text/csv",
    )


@device_bp.route(
    "/devices/<int:device_id>/upload",
    methods=["POST"],
)
def get_uploaded_file(device_id: int):
    file = request.files["file"]
    filename = secure_filename(file.filename)

    try:
        full_name = Device.query.get(device_id).full_name
        directory = Path(
            f"{upload_folder}/{full_name}",
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
        make_graph(device, "full")
        make_graph(device, "recent")
        return get_device_template(device_id, message="Файл успешно получен")

    except Exception:
        return get_device_template(
            device_id, error="Ошибка при загрузке файла"
        )
