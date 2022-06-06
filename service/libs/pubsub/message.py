import json


class Message:
    def __init__(self, climate_csv, cities_csv):
        self.climate_csv = climate_csv
        self.cities_csv = cities_csv

    def to_json(self):
        return json.dumps(
            {
                "message": {
                    "data": {
                        "climate_csv": self.climate_csv,
                        "cities_csv": self.cities_csv,
                    }
                }
            },
        )
