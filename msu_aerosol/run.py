from flask import Flask

from homepage.views import home_bp
from msu_aerosol import config
from msu_aerosol.admin import init_admin
from msu_aerosol.graph_funcs import make_graph, preprocessing_all_files
from msu_aerosol.models import db

__all__: list = []

app: Flask = config.initialize_flask_app(__name__)
app.register_blueprint(home_bp, name="home")
init_admin(app)
db.init_app(app)

with app.app_context():
    db.create_all()


def main() -> None:
    preprocessing_all_files()
    make_graph("AE33-S09-01249")
    make_graph("TCA08")
    make_graph("Web_MEM")
    make_graph("LVS")
    make_graph("PNS")
    app.run()


if __name__ == "__main__":
    main()
