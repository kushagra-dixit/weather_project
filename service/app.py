import socket

from flask import Flask
from flask_redoc import Redoc
from werkzeug.debug import DebuggedApplication

from .api import apispec, healthcheck, weather
from .config import Config
from .libs.exception_handler import exception_handler

SERVICE_PORT = 9999


def create_app(config_class=Config):
    """
    Create a Flask application using the app factory pattern.

    :return: Flask app
    """
    app = Flask(__name__)

    app.config.from_object(Config)

    app.register_blueprint(healthcheck)
    app.register_blueprint(apispec)
    app.register_blueprint(exception_handler)
    app.register_blueprint(weather)

    app.config["REDOC"] = {
        "spec_route": "/",
        "title": "API spec",
    }
    Redoc(app, "../openapi.yaml")

    if app.debug:
        app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)

    return app


# The default behaviour is use_reloader=True, but we need to be able to set it to False for the debugger to run.
def run(app, use_reloader=True):
    """
    Runs the flask application
    """
    app.run(
        host=socket.gethostbyname(socket.gethostname()),
        port=int(SERVICE_PORT),
        use_reloader=use_reloader,
    )


app = create_app()
