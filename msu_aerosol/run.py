from config import DEBUG, SQLALCHEMY_DATABASE_URI, STATIC_URL
from flask import Flask
from graph_funcs import make_graph, preprocessing_all_files

from homepage.views import home_bp

__all__ = ["main"]

app = Flask(__name__)

app.static_folder = STATIC_URL
app.debug = DEBUG
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI

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
