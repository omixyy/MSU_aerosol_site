from homepage.home import home_bp
from flask import Flask
from config import STATIC_URL
from graph_funcs import preprocessing_all_files, make_graph

app = Flask(__name__)
app.static_folder = STATIC_URL
app.register_blueprint(home_bp)


if __name__ == "__main__":
    preprocessing_all_files()
    make_graph('AE33-S09-01249')
    make_graph('TCA08')
    make_graph('Web_MEM')
    make_graph('LVS')
    make_graph('PNS')
    app.run(debug=True)
