from config import DEBUG, STATIC_URL
from flask import Flask
from graph_funcs import make_graph, preprocessing_all_files

from devices.data import db_session
from devices.device import device_bp

from homepage.home import home_bp

__all__ = ["main"]

app = Flask(__name__)

app.static_folder = STATIC_URL
app.debug = DEBUG

app.register_blueprint(home_bp, name="home")
app.register_blueprint(device_bp, name="devices")


def main() -> None:
    preprocessing_all_files()
    make_graph("AE33-S09-01249")
    make_graph("TCA08")
    make_graph("Web_MEM")
    make_graph("LVS")
    make_graph("PNS")
    db_session.global_init("devices/db/blogs.db")
    app.run()


if __name__ == "__main__":
    main()
