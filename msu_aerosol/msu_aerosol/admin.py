import csv
import json
import os
from pathlib import Path

from flask import Flask, request
from flask_admin import Admin
from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager

from msu_aerosol.models import (
    Complex,
    db,
    Device,
    TextFieldView,
    UserFieldView,
    User,
)
from msu_aerosol.graph_funcs import (
    preprocessing_one_file,
    make_graph,
)

__all__ = []


class AdminHomeView(AdminIndexView):
    def __init__(
        self,
        name=None,
        category=None,
        endpoint=None,
        url=None,
        template="admin/index.html",
        menu_class_name=None,
        menu_icon_type=None,
        menu_icon_value=None,
    ) -> None:
        super().__init__(
            name,
            category,
            endpoint,
            url,
            template,
            menu_class_name,
            menu_icon_type,
            menu_icon_value,
        )

    @expose("/", methods=["GET", "POST"])
    def create_settings_form(self) -> str:
        complex_to_devices: dict = get_complexes_dict()
        device_to_cols: dict = {}
        device_to_time_cols: dict = {}
        for _, devices in complex_to_devices.items():
            for dev in devices:
                dialect = get_dialect(
                    f"external_data/"
                    f"{dev}/"
                    f"{os.listdir(f'external_data/{dev}')[0]}",
                )

                with Path(
                    f"external_data/"
                    f"{dev}/"
                    f"{os.listdir(f'external_data/{dev}')[0]}",
                ).open("r") as csv_file:
                    header = list(csv.reader(csv_file, dialect=dialect))[0]
                    device_to_cols[dev] = list(
                        filter(
                            lambda x: "date" not in x.lower()
                            and "time" not in x.lower(),
                            header,
                        ),
                    )

                    device_to_time_cols[dev] = list(
                        filter(
                            lambda x: "date" in x.lower()
                            or "time" in x.lower(),
                            header,
                        ),
                    )
                
                with Path("msu_aerosol/config_devices.json").open("r") as config:
                    data = json.load(config)
                    if dev.name_on_disk not in data:
                        data[dev.name_on_disk] = {
                            "cols": [],
                            "time_cols": []
                        }
                        data[dev.name_on_disk]["cols"] = device_to_cols[dev]
                        data[dev.name_on_disk]["time_cols"] = device_to_time_cols[dev]
                        with Path("msu_aerosol/config_devices.json").open("w") as write_config:
                            json.dump(data, write_config, indent=2)
                        
                        # TODO: копировать файл из external_data в data

        if request.method == "GET":
            with Path("msu_aerosol/config_devices.json").open("r") as config:
                data = json.load(config)

        elif request.method == "POST":
            with Path("msu_aerosol/config_devices.json").open("w") as config:
                data = {
                    dev.name_on_disk: {
                        "time_cols": request.form.get(f"{dev.name}_rb"),
                        "cols": request.form.getlist(f"{dev.name}_cb"),
                        "format": request.form.get(
                            f"datetime_format_{dev.name}",
                        ),
                    }
                    for dev in Device.query.all()
                }
                json.dump(data, config, indent=2)

        return self.render(
            "admin/admin_home.html",
            device_to_cols=device_to_cols,
            device_to_time_cols=device_to_time_cols,
            data=data,
        )


admin: Admin = Admin(
    template_mode="bootstrap4",
    index_view=AdminHomeView(
        name="Home",
        template="admin/index.html",
        url="/admin",
    ),
)

login_manager: LoginManager = LoginManager()


def get_complexes_dict() -> dict:
    return {
        com: Device.query.filter(
            Device.complex_id == com.id,
        ).all()
        for com in Complex.query.all()
    }


def get_dialect(path: str) -> csv.Dialect:
    with Path(path).open("r") as f:
        return csv.Sniffer().sniff(f.readline())


def init_admin(app: Flask):
    login_manager.init_app(app)
    admin.init_app(app)
    admin.add_view(ModelView(Complex, db.session))
    admin.add_view(TextFieldView(Device, db.session))
    admin.add_view(UserFieldView(User, db.session))
