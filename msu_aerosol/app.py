import logging

from flask import Flask
from flask_restful import Api

from api.about import About
from api.archive import Archive, DeviceArchive
from api.contacts import Contacts
from api.homepage import Home
from api.users import Login, Logout, Profile, Register
from api.device import DeviceDownload, DevicePage, DeviceUpload
from msu_aerosol import config
from msu_aerosol.admin import init_admin, init_schedule
from msu_aerosol.commands import create_superuser
from msu_aerosol.models import db

__all__: list = []

app: Flask = config.initialize_flask_app(__name__)
api: Api = Api(app)
api.add_resource(Home, '/')
api.add_resource(About, '/about')
api.add_resource(Archive, '/archive')
api.add_resource(DeviceArchive, '/archive/<int:device_id>')
api.add_resource(Contacts, '/contacts')
api.add_resource(Profile, '/profile')
api.add_resource(Login, '/login')
api.add_resource(Register, '/register')
api.add_resource(Logout, '/logout')
api.add_resource(DevicePage, '/devices/<int:device_id>')
api.add_resource(DeviceDownload, '/devices/<int:device_id>/download')
api.add_resource(DeviceUpload, '/devices/<int:device_id>/upload')

app.cli.add_command(create_superuser)
app.logger.setLevel(logging.INFO)
log = logging.getLogger('werkzeug')
log.disabled = True
logging.getLogger('apscheduler.executors.default').propagate = False
logging.basicConfig(
    level=logging.INFO,
    filename='download_log.log',
    filemode='w',
)

with app.app_context():
    db.init_app(app)
    db.create_all()
    init_admin(app)
    init_schedule(None, None, None, app=app)


def main() -> None:
    app.run(use_reloader=False)


if __name__ == '__main__':
    main()
