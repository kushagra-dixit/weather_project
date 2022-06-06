import os

from flask import Blueprint
from werkzeug.exceptions import InternalServerError

from ...libs.logger import Logger

logger = Logger(__name__)

apispec = Blueprint("apispec", __name__)


@apispec.route("/apispec", methods=["GET"])
def redoc_documentation():
    try:
        script_dir = os.path.dirname(__file__)
        rel_path = "../../../openapi.yaml"
        abs_file_path = os.path.join(script_dir, rel_path)

        openapi_file = open(abs_file_path)
        documentation = openapi_file.read()
        openapi_file.close()

        return documentation
    except Exception as err:
        raise InternalServerError(str(err))
