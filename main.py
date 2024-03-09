from config import STATIC_URL, DEBUG
from flask import Flask
from graph_funcs import make_graph, preprocessing_all_files

from homepage.home import home_bp

app = Flask(__name__)
app.static_folder = STATIC_URL
app.debug = DEBUG
app.register_blueprint(home_bp)


if __name__ == "__main__":
    preprocessing_all_files()
    make_graph("AE33-S09-01249")
    make_graph("TCA08")
    make_graph("Web_MEM")
    make_graph("LVS")
    make_graph("PNS")
    app.run()
