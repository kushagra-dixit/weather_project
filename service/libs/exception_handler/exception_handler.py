from http import HTTPStatus

from flask import Blueprint, json
from werkzeug.exceptions import HTTPException

from ..logger import Logger

logger = Logger(__name__)

exception_handler = Blueprint("exception_handler", __name__)


@exception_handler.app_errorhandler(Exception)
def handle_errors(exception):
    """
    Handle all HTTP exceptions and return a JSON response
    """
    response = (
        HTTPStatus.INTERNAL_SERVER_ERROR.phrase,
        HTTPStatus.INTERNAL_SERVER_ERROR.value,
    )

    if isinstance(exception, HTTPException):
        json_exception = json.dumps(
            {
                "code": exception.code,
                "name": exception.name,
                "description": exception.description,
            }
        )
        logger.exception(json_exception)
        response = (exception.description or exception.name, exception.code)
    else:
        logger.exception(exception)

    return response
