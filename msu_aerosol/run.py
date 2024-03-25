from flask import Flask

from device.views import device_bp
from homepage.views import home_bp
from msu_aerosol import config
from msu_aerosol.admin import init_admin
from msu_aerosol.graph_funcs import make_graph, preprocessing_all_files
from msu_aerosol.models import db
from users.views import register_bp

__all__: list = []

app: Flask = config.initialize_flask_app(__name__)
app.register_blueprint(home_bp, name="home")
app.register_blueprint(device_bp, name="device_details")
app.register_blueprint(register_bp, name="registration")
init_admin(app)
db.init_app(app)

with app.app_context():
    preprocessing_all_files()
    make_graph("AE33-S09-01249")
    make_graph("LVS")
    make_graph("PNS")
    make_graph("TCA08")
    make_graph("Web_MEM")
    db.create_all()


def main() -> None:

    app.run()


if __name__ == "__main__":
    main()
