import http

from flask import Blueprint
from werkzeug.exceptions import InternalServerError

from ...libs.logger import Logger

logger = Logger(__name__)

healthcheck = Blueprint("healthcheck", __name__)


@healthcheck.route("/healthz/live", methods=["GET"])
def health_check_live():
    """
    Check whether the service is up and running.
    """
    try:
        return http.HTTPStatus.OK.phrase, http.HTTPStatus.OK.value
    except Exception as err:
        raise InternalServerError(str(err))


@healthcheck.route("/healthz/ready", methods=["GET"])
def health_check_ready():
    """
    Check whether the service is ready to receive requests.
    """
    try:
        return http.HTTPStatus.OK.phrase, http.HTTPStatus.OK.value
    except Exception as err:
        raise InternalServerError(str(err))
