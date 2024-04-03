import csv
import json
import os
from pathlib import Path
from typing import Type

from flask import Flask, request
from flask_admin import Admin
from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager
from sqlalchemy.event import listens_for

from msu_aerosol.graph_funcs import (
    download_device_data,
    make_graph,
    preprocess_device_data,
)
from msu_aerosol.models import (
    Complex,
    db,
    Device,
    DeviceView,
    User,
    UserFieldView,
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
    def admin_index(self) -> str:
        device_to_cols: dict = {}
        device_to_time_cols: dict = {}
        downloaded = os.listdir("data")
        downloaded.remove(".gitignore")
        if downloaded:
            for folder in downloaded:
                dialect = get_dialect(
                    f"data/" f"{folder}/" f"{os.listdir(f'data/{folder}')[0]}",
                )

                with Path(
                    f"data/" f"{folder}/" f"{os.listdir(f'data/{folder}')[0]}",
                ).open("r") as csv_file:
                    header = list(csv.reader(csv_file, dialect=dialect))[0]
                    device_to_cols[folder] = list(
                        filter(
                            lambda x: "date" not in x.lower()
                            and "time" not in x.lower(),
                            header,
                        ),
                    )

                    device_to_time_cols[folder] = list(
                        filter(
                            lambda x: "date" in x.lower()
                            or "time" in x.lower(),
                            header,
                        ),
                    )

                with Path(
                    "msu_aerosol/config_devices.json",
                ).open("r") as config:
                    data = json.load(config)
                    if folder not in data:
                        data[folder] = {
                            "cols": [],
                            "time_cols": [],
                        }
                        data[folder]["cols"] = device_to_cols[folder]
                        data[folder]["time_cols"] = device_to_time_cols[folder]
                with Path(
                    "msu_aerosol/config_devices.json",
                ).open("w") as write_config:
                    json.dump(data, write_config, indent=2)

        if request.method == "GET":
            with Path("msu_aerosol/config_devices.json").open("r") as config:
                data = json.load(config)

        elif request.method == "POST":
            with Path("msu_aerosol/config_devices.json").open("w") as config:
                data = {
                    dev_path: {
                        "time_cols": request.form.get(f"{dev_path}_rb"),
                        "cols": request.form.getlist(f"{dev_path}_cb"),
                        "format": request.form.get(
                            f"datetime_format_{dev_path}",
                        ),
                    }
                    for dev_path in downloaded
                }
                json.dump(data, config, indent=2)
            for device in [
                i
                for i in downloaded
                if "graph_" + i + ".html"
                not in os.listdir(
                    "templates/includes/devices/full",
                )
            ]:
                preprocess_device_data(device)
                make_graph(device)

            for dev in Device.query.all():
                dev.show = True
            db.session.commit()

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


def get_dialect(path: str) -> Type[csv.Dialect | csv.Dialect]:
    with Path(path).open("r") as f:
        return csv.Sniffer().sniff(f.readline())


@listens_for(Device, "after_insert")
def after_insert(mapper, connection, target):
    download_device_data(target.link)


def init_admin(app: Flask):
    login_manager.init_app(app)
    admin.init_app(app)
    admin.add_view(ModelView(Complex, db.session))
    admin.add_view(DeviceView(Device, db.session))
    admin.add_view(UserFieldView(User, db.session))
