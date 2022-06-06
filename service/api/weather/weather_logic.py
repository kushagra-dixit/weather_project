from xml.dom import ValidationErr
from ...libs.logger import Logger
from ...libs.data import data
from werkzeug.exceptions import BadRequest
import numpy as np




logger = Logger(__name__)


def get_temperature_data_of_city(date, city):
    temp_data_of_city = data.get_city_temp_data(date, city)

    if (temp_data_of_city is None) or (np.isnan(temp_data_of_city["mean_temp"])):
        return {"msg": "the data for the query is unavailable"}
    try:
        temperature_data_of_city = {
            "mean_temp_city": temp_data_of_city["mean_temp"],
            "median_temp_city": temp_data_of_city["median_temp"],
        }
        return temperature_data_of_city
    except TypeError:
        return {"msg": "please Fix query, city with first letter upper case like (City, Province) and date needs to be formatted exactly as (YYYY-MM-DD 0:00)"}


def get_temperature_data_of_all_urban(date):
    urban_temp_data=data.get_all_urban_temp_data(date)
    if (urban_temp_data is None) or (np.isnan(urban_temp_data["mean_temp"])):
        return {"msg": "the data for that date is unavailable, please select a date between Jan-feb 2021"}
    try:
        temperature_data_of_all_urban = {
            "mean_temp_all_urban": urban_temp_data["mean_temp"],
            "median_temp_all_urban": urban_temp_data["median_temp"],
        }
        return temperature_data_of_all_urban
    except TypeError:
        return {"msg": "please Fix query, city with first letter upper case like (City, Province) and date needs to be formatted exactly as (YYYY-MM-DD 0:00)"}


def add_row_to_climate(args):
    return_msg = data.add_row_to_climate_dataset(args)
    return return_msg


def process_results_dataset(process_msg):
    try:
        return_message = data.process_results_csv(process_msg["climate_csv"], process_msg["cities_csv"])
        return return_message
    except Exception as err:
        logger.debug("please fix cities and climate dataframe information")
        raise BadRequest(str(err))


