from genericpath import exists
from http import HTTPStatus
from flask import Blueprint, request, current_app
from jsonschema.exceptions import ValidationError
from werkzeug.exceptions import BadRequest

from ...libs.logger import Logger
import service.api.weather.weather_validation as validation
import service.api.weather.weather_logic as logic
import json
import base64


logger = Logger(__name__)


weather = Blueprint("weather", __name__)


@weather.route("/temp", methods=["GET"])
def get_temp():
    try:
        args = request.args.to_dict()
        validation.validate_get_temp(args)
        if "city" in args.keys():
            temperature_data_of_city = logic.get_temperature_data_of_city(
                args["date"], args["city"]
            )
            return temperature_data_of_city, HTTPStatus.OK.value

        else:
            temperature_data_of_all_urban = logic.get_temperature_data_of_all_urban(
                args["date"]
            )

            return temperature_data_of_all_urban, HTTPStatus.OK.value

    except ValidationError as err:
        raise BadRequest(str(err))


@weather.route("/append_climate_row", methods=["POST"])
def post_row():
    try:
        args = request.args.to_dict()
        validation.validate_append_climate_row(args)
        response_msg = logic.add_row_to_climate(args)
        return response_msg, HTTPStatus.OK.value

    except ValidationError as err:
        raise BadRequest(str(err))


@weather.route("/process_results", methods=["POST"])
def process_results():
    try:
        envelope = request.get_json()
        logger.info(f"envelope: {envelope}")
        if not envelope:
            msg = "no Pub/Sub message received"
            raise BadRequest(str(msg))

        if not isinstance(envelope, dict) or "message" not in envelope:
            msg = "invalid Pub/Sub message format"
            raise BadRequest(str(msg))
        pubsub_message = envelope["message"]

        logger.info(f"message payload: {pubsub_message}")
        if isinstance(pubsub_message, dict) and "data" in pubsub_message:
            try:
                process_message = (
                    base64.b64decode(pubsub_message["data"]).decode("utf-8").strip()
                )
                process_message_json = json.loads(process_message)
            # For testing through postman and local development
            except TypeError:
                process_message_json = pubsub_message["data"]

            logger.info(process_message_json)
            msg = logic.process_results_dataset(process_message_json)

            return msg, HTTPStatus.OK.value

    except ValidationError as err:
        raise BadRequest(str(err))

