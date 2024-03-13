from flask import Flask
from msu_aerosol.admin import init_admin
from msu_aerosol.config import DEBUG, SECRET_KEY, STATIC_URL
from msu_aerosol.graph_funcs import make_graph, preprocessing_all_files
from msu_aerosol.models import db

from homepage.views import home_bp

__all__ = ["main"]

app = Flask(__name__)
app.static_folder = STATIC_URL
app.debug = DEBUG
app.secret_key = SECRET_KEY

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db.init_app(app)

init_admin(app)
with app.app_context():
    db.create_all()

app.register_blueprint(home_bp, name="home")


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
