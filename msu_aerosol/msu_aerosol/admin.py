from flask import Flask
from flask_admin import Admin
from flask_admin import AdminIndexView
from flask_admin.contrib.sqla import ModelView

from msu_aerosol.models import (
    Complex,
    db,
    Device,
    TextFieldView,
)

__all__ = ["init_admin"]

admin: Admin = Admin(
    index_view=AdminIndexView(
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
