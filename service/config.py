import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    GCLOUD_PROJECT = os.environ["GCLOUD_PROJECT"]
    DATA_LAKE_BUCKET = os.environ["DATA_LAKE_BUCKET"]
    CITIES_DATASET = os.environ["CITIES_DATASET"]
    CLIMATE_DATASET = os.environ["CLIMATE_DATASET"]
    PROCESS_RESULT_TOPIC = os.environ["PROCESS_RESULT_TOPIC"]
    RESULTS_DATASET = os.environ["RESULTS_DATASET"]
    LOCAL_RUN = os.environ["LOCAL_RUN"]
    if str(LOCAL_RUN) == "True":
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcs-key.json"

    # Configuration
    