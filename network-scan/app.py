import os

from flask import Flask, render_template
from network_scan import network_scan


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route("/")
    def index():
        address, network = network_scan()
        return render_template("index.html", address=address, network=network)

    return app


def main():
    create_app().run()


if __name__ == "__main__":
    main()
