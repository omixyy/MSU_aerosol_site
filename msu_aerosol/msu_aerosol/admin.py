from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from msu_aerosol.models import Complex, db, Device

__all__ = ["init_admin"]

admin: Admin = Admin()


def init_admin(app: Flask):
    admin.init_app(app)
    admin.add_view(ModelView(Complex, db.session))
    admin.add_view(ModelView(Device, db.session))
