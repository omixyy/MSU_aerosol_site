import json
from pathlib import Path

from flask import Flask
from flask_admin import Admin
from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView

from msu_aerosol.models import (
    Complex,
    db,
    Device,
    TextFieldView,
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
        all_devices = Device.query.all()
        with Path("msu_aerosol/config_devices.json", "r").open() as jsonf:
            data = json.load(jsonf)
            cols = {dev: data[dev]["cols"] for dev in data.keys()}
            print(cols)
            time_cols = {dev: data[dev]["time_cols"] for dev in data.keys()}
        return self.render(
            "admin/admin_home.html",
            devices=all_devices,
            time_cols=time_cols,
            cols=cols,
        )


admin: Admin = Admin(
    template_mode="bootstrap4",
    index_view=AdminHomeView(
        name="Home",
        template="admin/index.html",
        url="/admin",
    ),
)


def get_complexes_dict() -> dict:
    return {
        com: Device.query.filter(
            Device.complex_id == com.id,
        ).all()
        for com in Complex.query.all()
    }


def init_admin(app: Flask):
    admin.init_app(app)
    admin.add_view(ModelView(Complex, db.session))
    admin.add_view(TextFieldView(Device, db.session))
