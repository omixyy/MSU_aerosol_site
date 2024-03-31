from flask import Flask

from msu_aerosol import config
from msu_aerosol.admin import init_admin
from msu_aerosol.models import db
from views.device import device_bp
from views.homepage import home_bp
from views.users import login_bp, register_bp
from views.users import profile_bp

__all__: list = []

app: Flask = config.initialize_flask_app(__name__)
app.register_blueprint(home_bp, name="home")
app.register_blueprint(device_bp, name="device_details")
app.register_blueprint(register_bp, name="registration")
app.register_blueprint(login_bp, name="login")
app.register_blueprint(profile_bp, name="profile")
init_admin(app)
db.init_app(app)
db.session.permanent = True

with app.app_context():
    db.create_all()


def main() -> None:
    app.run()


if __name__ == "__main__":
    main()
