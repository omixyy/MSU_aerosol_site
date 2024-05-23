import logging

from flask import Flask

from msu_aerosol import config
from msu_aerosol.admin import init_admin, init_schedule
from msu_aerosol.commands import create_superuser
from msu_aerosol.models import db
from views.about import about_bp
from views.archive import archive_bp
from views.contacts import contacts_bp
from views.device import device_bp
from views.homepage import home_bp
from views.users import login_bp, register_bp
from views.users import profile_bp

__all__: list = []

app: Flask = config.initialize_flask_app(__name__)
app.register_blueprint(home_bp, name='home')
app.register_blueprint(device_bp, name='device_details')
app.register_blueprint(register_bp, name='registration')
app.register_blueprint(login_bp, name='login')
app.register_blueprint(profile_bp, name='profile')
app.register_blueprint(about_bp, name='about')
app.register_blueprint(archive_bp, name='archive')
app.register_blueprint(contacts_bp, name='contacts')

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
