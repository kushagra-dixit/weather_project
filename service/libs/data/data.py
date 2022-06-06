import pandas as pd
import numpy as np
from geopy import distance
from flask import current_app
import os
import requests
import backoff
from google.cloud import storage
from ..logger import Logger
# from ...config import Config
from ...libs.pubsub import Message, publish_message

logger = Logger(__name__)
# config = Config()

# PROCESS_RESULT_TOPIC = current_app.config["PROCESS_RESULT_TOPIC"]
# GCLOUD_PROJECT = current_app.config["GCLOUD_PROJECT"]
# DATA_LAKE_BUCKET = current_app.config["DATA_LAKE_BUCKET"]
# CLIMATE_DATASET_PATH = current_app.config["CLIMATE_DATASET"]
# CITIES_DATASET_PATH = current_app.config["CITIES_DATASET"]
# RESULTS_DATASET_PATH = current_app.config["RESULTS_DATASET"]  # "results.csv"
# CLIENT = storage.Client()
# BUCKET = CLIENT.get_bucket(DATA_LAKE_BUCKET)
POPULATION_THRESH = 10000
MAX_TIME_RETRY = 60
BATCH_PROCESSING_CONDITION = 5000


@backoff.on_exception(
    backoff.expo,
    (requests.exceptions.Timeout, requests.exceptions.ConnectionError),
    max_time=MAX_TIME_RETRY,
)
def get_city_temp_data(date, city):
    try:
        logger.info("opening results df")
        results_bucket_path= current_app.config["RESULTS_DATASET"]
        DATA_LAKE_BUCKET = current_app.config["DATA_LAKE_BUCKET"]
        results_dataset_path = f"gs://{DATA_LAKE_BUCKET}/{results_bucket_path}"
        results_df = pd.read_csv(results_dataset_path)
        # logger.info(results_df)
        logger.info(f"querying the dataset for {city} on {date}")
        city_mean_temp = float(
            results_df[(results_df["DATE"] == date) & (results_df["CITY"] == city)][
                "MEAN_TEMP"
            ].values[0]
        )
        city_median_temp = float(
            results_df[(results_df["DATE"] == date) & (results_df["CITY"] == city)][
                "MEDIAN_TEMP"
            ].values[0]
        )
        logger.info("results obtained")
        
        return {"mean_temp":city_mean_temp,"median_temp":city_median_temp}

    except Exception as e:
        logger.debug(f"{e} error related to uploading files")


@backoff.on_exception(
    backoff.expo,
    (requests.exceptions.Timeout, requests.exceptions.ConnectionError),
    max_time=MAX_TIME_RETRY,
)
def get_all_urban_temp_data(date):
    try:
        logger.info("opening results df")
        results_bucket_path=current_app.config["RESULTS_DATASET"]
        DATA_LAKE_BUCKET = current_app.config["DATA_LAKE_BUCKET"]
        results_dataset_path = f"gs://{DATA_LAKE_BUCKET}/{results_bucket_path}"
        results_df = pd.read_csv(results_dataset_path)
        # logger.info(results_df)
        logger.info(f"querying the dataset for all cities on {date}")
        all_urban_mean_temp = np.nanmean(results_df[results_df['DATE'] == date]["MEAN_TEMP"])
        all_urban_median_temp = np.nanmedian(results_df[results_df['DATE'] == date]["MEDIAN_TEMP"])
        logger.info("results obtained")
        
        return {"mean_temp":all_urban_mean_temp,"median_temp":all_urban_median_temp}

    except Exception as e:
        logger.debug(f"{e} error related to uploading files")

@backoff.on_exception(
    backoff.expo,
    (requests.exceptions.Timeout, requests.exceptions.ConnectionError),
    max_time=MAX_TIME_RETRY,
)
def process_results_csv(climate_dataset_file, cities_dataset_file):
    # loading datasets into dataframes
    logger.info("loading data")
    DATA_LAKE_BUCKET = current_app.config["DATA_LAKE_BUCKET"]
    cities_dataset_path = f"gs://{DATA_LAKE_BUCKET}/{cities_dataset_file}"
    climate_dataset_path = f"gs://{DATA_LAKE_BUCKET}/{climate_dataset_file}"
    cities_df = pd.read_csv(cities_dataset_path)
    climate_df = pd.read_csv(climate_dataset_path)

    logger.info("climate data cleanup")
    # grouping lat, long to a particular dataframe
    climate_df["coord"] = list(zip(climate_df["lat"], climate_df["lng"]))
    station_lat_long = pd.DataFrame(
        list(climate_df.groupby(["STATION_NAME", "coord"]).groups),
        columns=["STATION_NAME", "COORD"],
    )
    station_lat_long.drop_duplicates(
        subset=["STATION_NAME"], keep="first", inplace=True
    )
    station_lat_long.set_index(["STATION_NAME"], inplace=True)

    # processing cities dataframe to filter for location and population threshold

    logger.info("city data cleanup")
    cities_df[cities_df.duplicated(subset=["city"], keep=False)]
    cities_df["location"] = cities_df["city"] + str(", ") + cities_df["admin"]
    cities_df["coord"] = list(zip(cities_df["lat"], cities_df["lng"]))
    cities_df = cities_df[cities_df["population_proper"] > POPULATION_THRESH]

    city_lat_long = pd.DataFrame(
        list(cities_df.groupby(["location", "coord"]).groups),
        columns=["LOCATION", "COORD"],
    )
    city_lat_long.set_index(["LOCATION"], inplace=True)
    city_station_distance = pd.DataFrame(
        index=city_lat_long.index, columns=station_lat_long.index
    )
    

    logger.info("Core processing station mean and median temp")
    for city, city_row in city_station_distance.iterrows():
        for station, distance_km in city_row.items():
            city_station_distance.loc[city, station] = distance.distance(
                city_lat_long.loc[city, "COORD"], station_lat_long.loc[station, "COORD"]
            ).km
    city_station_distance = city_station_distance.astype(float)
    city_col = list(city_station_distance.index)
    date_col = list(climate_df["LOCAL_DATE"].unique())
    results_df = pd.DataFrame(
        index=[city_col * len(date_col), date_col * len(city_col)],
        columns=["STATIONS", "MEAN_TEMP", "MEDIAN_TEMP"],
    )

    logger.info("associating stations to locations")
    for city in city_col:
        city_row = city_station_distance.filter(items=[city], axis=0)
        stations = city_row.loc[:, ~(city_row > 40).any()]
        if stations.shape[1] == 0:
            stations = city_row.loc[:, city_row.idxmin(axis=1)]
        climate_df_city = climate_df[
            (climate_df["STATION_NAME"].isin(list(stations.columns)))
        ]
        results_df.index.names=["CITY","DATE"]
        for date in date_col:
            climate_df_city_date = climate_df_city[
                climate_df_city["LOCAL_DATE"] == date
            ]
            results_df.loc[(city, date), "STATIONS"] = ", ".join(list(stations.columns))
            results_df.loc[(city, date), "MEAN_TEMP"] = np.nanmean(
                climate_df_city_date["MEAN_TEMPERATURE"]
            )
            results_df.loc[(city, date), "MEDIAN_TEMP"] = np.nanmedian(
                climate_df_city_date["MEAN_TEMPERATURE"]
            )
        
    logger.info("saving file as a csv")
    results_df.to_csv(current_app.config["RESULTS_DATASET"])
    logger.info("writing files to gcs")
    CLIENT = storage.Client()
    BUCKET = CLIENT.get_bucket(DATA_LAKE_BUCKET)
    blob = BUCKET.blob(current_app.config["RESULTS_DATASET"])
    blob.upload_from_filename(current_app.config["RESULTS_DATASET"])

    return {"msg": "results have been processed and uploaded"}

@backoff.on_exception(
    backoff.expo,
    (requests.exceptions.Timeout, requests.exceptions.ConnectionError),
    max_time=MAX_TIME_RETRY,
)
def add_row_to_climate_dataset(args):
    lng = args["lng"]
    lat = args["lat"]
    STATION_NAME = args["STATION_NAME"]
    CLIMATE_IDENTIFIER = args["CLIMATE_IDENTIFIER"]
    ID = args["ID"]
    LOCAL_DATE = args["LOCAL_DATE"]
    PROVINCE_CODE = args["PROVINCE_CODE"]
    LOCAL_YEAR = args["LOCAL_YEAR"]
    LOCAL_MONTH = args["LOCAL_MONTH"]
    LOCAL_DAY = args["LOCAL_DAY"]
    try:
        MEAN_TEMPERATURE = args["MEAN_TEMPERATURE"]
    except KeyError:
        MEAN_TEMPERATURE = ""
    try:
        MEAN_TEMPERATURE_FLAG = args["MEAN_TEMPERATURE_FLAG"]
    except KeyError:
        MEAN_TEMPERATURE_FLAG = ""
    try:
        MIN_TEMPERATURE = args["MIN_TEMPERATURE"]
    except KeyError:
        MIN_TEMPERATURE = ""
    try:
        MIN_TEMPERATURE_FLAG = args["MIN_TEMPERATURE_FLAG"]
    except KeyError:
        MIN_TEMPERATURE_FLAG = ""
    try:
        MAX_TEMPERATURE = args["MAX_TEMPERATURE"]
    except KeyError:
        MAX_TEMPERATURE = ""
    try:
        MAX_TEMPERATURE_FLAG = args["MAX_TEMPERATURE_FLAG"]
    except KeyError:
        MAX_TEMPERATURE_FLAG = ""

    try:
        TOTAL_PRECIPITATION = args["TOTAL_PRECIPITATION"]
    except KeyError:
        TOTAL_PRECIPITATION = ""

    try:
        TOTAL_PRECIPITATION_FLAG = args["TOTAL_PRECIPITATION_FLAG"]
    except KeyError:
        TOTAL_PRECIPITATION_FLAG = ""

    try:
        TOTAL_RAIN = args["TOTAL_RAIN"]
    except KeyError:
        TOTAL_RAIN = ""

    try:
        TOTAL_RAIN_FLAG = args["TOTAL_RAIN_FLAG"]
    except KeyError:
        TOTAL_RAIN_FLAG = ""
    try:
        TOTAL_SNOW = args["TOTAL_SNOW"]
    except KeyError:
        TOTAL_SNOW = ""

    try:
        TOTAL_SNOW_FLAG = args["TOTAL_SNOW_FLAG"]
    except KeyError:
        TOTAL_SNOW_FLAG = ""

    try:
        SNOW_ON_GROUND = args["SNOW_ON_GROUND"]
    except KeyError:
        SNOW_ON_GROUND = ""

    try:
        SNOW_ON_GROUND_FLAG = args["SNOW_ON_GROUND_FLAG"]
    except KeyError:
        SNOW_ON_GROUND_FLAG = ""

    try:
        DIRECTION_MAX_GUST = args["DIRECTION_MAX_GUST"]
    except KeyError:
        DIRECTION_MAX_GUST = ""
    try:
        DIRECTION_MAX_GUST_FLAG = args["DIRECTION_MAX_GUST_FLAG"]
    except KeyError:
        DIRECTION_MAX_GUST_FLAG = ""

    try:
        SPEED_MAX_GUST = args["SPEED_MAX_GUST"]
    except KeyError:
        SPEED_MAX_GUST = ""

    try:
        SPEED_MAX_GUST_FLAG = args["SPEED_MAX_GUST_FLAG"]
    except KeyError:
        SPEED_MAX_GUST_FLAG = ""

    try:
        COOLING_DEGREE_DAYS = args["COOLING_DEGREE_DAYS"]
    except KeyError:
        COOLING_DEGREE_DAYS = ""

    try:
        COOLING_DEGREE_DAYS_FLAG = args["COOLING_DEGREE_DAYS_FLAG"]
    except KeyError:
        COOLING_DEGREE_DAYS_FLAG = ""

    try:
        HEATING_DEGREE_DAYS = args["HEATING_DEGREE_DAYS"]
    except KeyError:
        HEATING_DEGREE_DAYS = ""

    try:
        HEATING_DEGREE_DAYS_FLAG = args["HEATING_DEGREE_DAYS_FLAG"]
    except KeyError:
        HEATING_DEGREE_DAYS_FLAG = ""

    try:
        MIN_REL_HUMIDITY = args["MIN_REL_HUMIDITY"]
    except KeyError:
        MIN_REL_HUMIDITY = ""

    try:
        MIN_REL_HUMIDITY_FLAG = args["MIN_REL_HUMIDITY_FLAG"]
    except KeyError:
        MIN_REL_HUMIDITY_FLAG = ""

    try:
        MAX_REL_HUMIDITY = args["MAX_REL_HUMIDITY"]
    except KeyError:
        MAX_REL_HUMIDITY = ""

    try:
        MAX_REL_HUMIDITY_FLAG = args["MAX_REL_HUMIDITY_FLAG"]
    except KeyError:
        MAX_REL_HUMIDITY_FLAG = ""
    new_climate_row = {
        "lng": lng,
        "lat": lat,
        "STATION_NAME": STATION_NAME,
        "CLIMATE_IDENTIFIER": CLIMATE_IDENTIFIER,
        "ID": ID,
        "LOCAL_DATE": LOCAL_DATE,
        "PROVINCE_CODE": PROVINCE_CODE,
        "LOCAL_YEAR": LOCAL_YEAR,
        "LOCAL_MONTH": LOCAL_MONTH,
        "LOCAL_DAY": LOCAL_DAY,
        "MEAN_TEMPERATURE": MEAN_TEMPERATURE,
        "MEAN_TEMPERATURE_FLAG": MEAN_TEMPERATURE_FLAG,
        "MIN_TEMPERATURE": MIN_TEMPERATURE,
        "MIN_TEMPERATURE_FLAG": MIN_TEMPERATURE_FLAG,
        "MAX_TEMPERATURE": MAX_TEMPERATURE,
        "MAX_TEMPERATURE_FLAG": MAX_TEMPERATURE_FLAG,
        "TOTAL_PRECIPITATION": TOTAL_PRECIPITATION,
        "TOTAL_PRECIPITATION_FLAG": TOTAL_PRECIPITATION_FLAG,
        "TOTAL_RAIN": TOTAL_RAIN,
        "TOTAL_RAIN_FLAG": TOTAL_RAIN_FLAG,
        "TOTAL_SNOW": TOTAL_SNOW,
        "TOTAL_SNOW_FLAG": TOTAL_SNOW_FLAG,
        "SNOW_ON_GROUND": SNOW_ON_GROUND,
        "SNOW_ON_GROUND_FLAG": SNOW_ON_GROUND_FLAG,
        "DIRECTION_MAX_GUST": DIRECTION_MAX_GUST,
        "DIRECTION_MAX_GUST_FLAG": DIRECTION_MAX_GUST_FLAG,
        "SPEED_MAX_GUST": SPEED_MAX_GUST,
        "SPEED_MAX_GUST_FLAG": SPEED_MAX_GUST_FLAG,
        "COOLING_DEGREE_DAYS": COOLING_DEGREE_DAYS,
        "COOLING_DEGREE_DAYS_FLAG": COOLING_DEGREE_DAYS_FLAG,
        "HEATING_DEGREE_DAYS": HEATING_DEGREE_DAYS,
        "HEATING_DEGREE_DAYS_FLAG": HEATING_DEGREE_DAYS_FLAG,
        "MIN_REL_HUMIDITY": MIN_REL_HUMIDITY,
        "MIN_REL_HUMIDITY_FLAG": MIN_REL_HUMIDITY_FLAG,
        "MAX_REL_HUMIDITY": MAX_REL_HUMIDITY,
        "MAX_REL_HUMIDITY_FLAG": MAX_REL_HUMIDITY_FLAG,
    }
    try:
        logger.info("opening climate file to add row")
        DATA_LAKE_BUCKET = current_app.config["DATA_LAKE_BUCKET"]
        CLIMATE_DATASET_PATH = current_app.config["CLIMATE_DATASET"]

        climate_dataset_path = f"gs://{DATA_LAKE_BUCKET}/{CLIMATE_DATASET_PATH}"
        climate_df = pd.read_csv(climate_dataset_path)
        climate_dataset_update = climate_df.append(new_climate_row,ignore_index=True)
        number_of_rows = climate_df.shape[0]
        logger.info(f"{number_of_rows} are in the climate dataframe")
        climate_dataset_update.to_csv("CLIMATE_DATASET_PATH_TEMP", index=False)
        CLIENT = storage.Client()
        BUCKET = CLIENT.get_bucket(DATA_LAKE_BUCKET)
        new_climate_dataset_path = BUCKET.blob(CLIMATE_DATASET_PATH)
        new_climate_dataset_path.upload_from_filename("CLIMATE_DATASET_PATH_TEMP")

        if number_of_rows % BATCH_PROCESSING_CONDITION == 0:
            message = Message(current_app.config["CLIMATE_DATASET"], current_app.config["CITIES_DATASET"])
            publish_message(
                message.to_json(), current_app.config["GCLOUD_PROJECT"], current_app.config["PROCESS_RESULT_TOPIC"]
            )
            return {"msg": "row added and msg sent for batch processing"}

        return {"msg":"row appended"}
    except Exception as e:
        logger.debug(f"{e} error related to uploading files")
        raise Exception


