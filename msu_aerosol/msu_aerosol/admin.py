import csv
import json
import os
from pathlib import Path
import shutil
from typing import Type

from flask import Flask, request
from flask_admin import Admin
from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager
import plotly.express as px
from sqlalchemy.event import listens_for

from msu_aerosol.graph_funcs import (
    disk,
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
        device_to_time_col: dict = {}
        downloaded = os.listdir("data")
        downloaded.remove(".gitignore")
        if downloaded:
            for folder in downloaded:
                file: str = os.listdir(f"data/{folder}")[0]
                dialect = get_dialect(f"data/{folder}/{file}")
                with Path(f"data/{folder}/{file}").open("r") as csv_file:
                    header = list(csv.reader(csv_file, dialect=dialect))[0]
                    device_to_cols[folder] = list(
                        filter(
                            lambda x: "date" not in x.lower()
                            and "time" not in x.lower(),
                            header,
                        ),
                    )

                    device_to_time_col[folder] = list(
                        filter(
                            lambda x: "date" in x.lower()
                            or "time" in x.lower(),
                            header,
                        ),
                    )

                with Path("msu_aerosol/config_devices.json").open("r") as cfg:
                    data = json.load(cfg)
                    if folder not in data:
                        data[folder] = {
                            "cols": [],
                            "time_cols": [],
                        }
                        data[folder]["cols"] = device_to_cols[folder]
                        data[folder]["time_cols"] = device_to_time_col[folder]

                with Path("msu_aerosol/config_devices.json").open("w") as cfg:
                    json.dump(data, cfg, indent=2)

        if request.method == "GET":
            with Path("msu_aerosol/config_devices.json").open("r") as config:
                data = json.load(config)

        elif request.method == "POST":
            with Path("msu_aerosol/config_devices.json").open("w") as config:
                colors = px.colors.qualitative.Alphabet
                data = {
                    dev_path: {
                        "time_cols": request.form.get(f"{dev_path}_rb"),
                        "cols": request.form.getlist(f"{dev_path}_cb"),
                        "format": request.form.get(
                            f"datetime_format_{dev_path}",
                        ),
                        "color_dict": {
                            device_to_cols[dev_path][i]: colors[i]
                            for i in range(len(request.form.getlist(f"{dev_path}_cb")))
                        },
                    }
                    for dev_path in downloaded
                }

                json.dump(data, config, indent=2)

            full: list = os.listdir("templates/includes/devices/full")
            for device in list(
                filter(lambda x: f"graph_{x}.html" not in full, downloaded),
            ):
                preprocess_device_data(device)
                make_graph(device, "full")
                make_graph(device, "recent")

            for dev in Device.query.all():
                dev.show = True

            db.session.commit()

        return self.render(
            "admin/admin_home.html",
            device_to_cols=device_to_cols,
            device_to_time_cols=device_to_time_col,
            data=data,
        )


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
def after_insert(mapper, connection, target) -> None:
    download_device_data(target.link)


@listens_for(Device, "after_delete")
def after_delete(mapper, connection, target) -> None:
    with Path("msu_aerosol/config_devices.json").open("r") as config:
        data = json.load(config)
        full_name = disk.get_public_meta(target.link)["name"]
        del data[full_name]
        if Path(f"data/{full_name}").exists():
            shutil.rmtree(f"data/{full_name}")
    with Path("msu_aerosol/config_devices.json").open("w") as config:
        json.dump(data, config, indent=2)

    graph_full = f"templates/includes/devices/full/graph_{full_name}.html"
    graph_rec = f"templates/includes/devices/recent/graph_{full_name}.html"
    proc_data = f"proc_data/{full_name}"
    if Path(graph_full).exists():
        Path(graph_full).unlink()

    if Path(graph_rec).exists():
        Path(graph_rec).unlink()

    if Path(proc_data).exists():
        shutil.rmtree(proc_data)


admin: Admin = Admin(
    template_mode="bootstrap4",
    index_view=AdminHomeView(
        name="Home",
        template="admin/index.html",
        url="/admin",
    ),
)

login_manager: LoginManager = LoginManager()


def init_admin(app: Flask):
    login_manager.init_app(app)
    admin.init_app(app)
    admin.add_view(ModelView(Complex, db.session))
    admin.add_view(DeviceView(Device, db.session))
    admin.add_view(UserFieldView(User, db.session))
