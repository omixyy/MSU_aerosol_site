from msu_aerosol.config import DEBUG, STATIC_URL
from flask import Flask
from msu_aerosol.graph_funcs import make_graph, preprocessing_all_files

from homepage.views import home_bp

__all__ = ["main"]

app = Flask(__name__)
app.static_folder = STATIC_URL
app.debug = DEBUG

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
