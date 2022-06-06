from jsonschema import validate


GET_TEMP_VALIDATION_SCHEMA = {
    "type": "object",
    "properties": {
        "date": {"type": "string"},
        "city": {"type": "string"},
    },
    "additionalProperties": False,
    "required": ["date"],
}

APPEND_CLIMATE_ROW_SCHEMA = {
    "type": "object",
    "properties": {
        "lng": {"type": "string"},
        "lat": {"type": "string"},
        "STATION_NAME": {"type": "string"},
        "CLIMATE_IDENTIFIER": {"type": "string"},
        "ID": {"type": "string"},
        "LOCAL_DATE": {"type": "string"},
        "PROVINCE_CODE": {"type": "string"},
        "LOCAL_YEAR": {"type": "string"},
        "LOCAL_MONTH": {"type": "string"},
        "LOCAL_DAY": {"type": "string"},
        "MEAN_TEMPERATURE": {"type": "string"},
        "MEAN_TEMPERATURE_FLAG": {"type": "string"},
        "MIN_TEMPERATURE": {"type": "string"},
        "MIN_TEMPERATURE_FLAG": {"type": "string"},
        "MAX_TEMPERATURE": {"type": "string"},
        "MAX_TEMPERATURE_FLAG": {"type": "string"},
        "TOTAL_PRECIPITATION": {"type": "string"},
        "TOTAL_PRECIPITATION_FLAG": {"type": "string"},
        "TOTAL_RAIN": {"type": "string"},
        "TOTAL_RAIN_FLAG": {"type": "string"},
        "TOTAL_SNOW": {"type": "string"},
        "TOTAL_SNOW_FLAG": {"type": "string"},
        "SNOW_ON_GROUND": {"type": "string"},
        "SNOW_ON_GROUND_FLAG": {"type": "string"},
        "DIRECTION_MAX_GUST": {"type": "string"},
        "DIRECTION_MAX_GUST_FLAG": {"type": "string"},
        "SPEED_MAX_GUST": {"type": "string"},
        "SPEED_MAX_GUST_FLAG": {"type": "string"},
        "COOLING_DEGREE_DAYS": {"type": "string"},
        "COOLING_DEGREE_DAYS_FLAG": {"type": "string"},
        "HEATING_DEGREE_DAYS": {"type": "string"},
        "HEATING_DEGREE_DAYS_FLAG": {"type": "string"},
        "MIN_REL_HUMIDITY": {"type": "string"},
        "MIN_REL_HUMIDITY_FLAG": {"type": "string"},
        "MAX_REL_HUMIDITY": {"type": "string"},
        "MAX_REL_HUMIDITY_FLAG": {"type": "string"},
    },
    "additionalProperties": False,
    "required": [
        "lng",
        "lat",
        "STATION_NAME",
        "CLIMATE_IDENTIFIER",
        "ID",
        "LOCAL_DATE",
        "PROVINCE_CODE",
        "LOCAL_YEAR",
        "LOCAL_MONTH",
        "LOCAL_DAY",
    ],
}
PROCESS_RESULTS_VALIDATION_SCHEMA = {
    "type": "object",
    "properties": {
        "climate_csv": {"type": "string"},
        "cities_csv": {"type": "string"},
    },
    "additionalProperties": False,
    "required": ["climate_csv", "cities_csv"],
}


def validate_get_temp(args):
    validate(args, GET_TEMP_VALIDATION_SCHEMA)


def validate_append_climate_row(body):
    validate(body, APPEND_CLIMATE_ROW_SCHEMA)


def validate_process_results(body):
    validate(body, PROCESS_RESULTS_VALIDATION_SCHEMA)
