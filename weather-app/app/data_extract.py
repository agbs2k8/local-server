import json
import datetime
import string
import requests
import logging
import logging.config


def get_air_quality(cfg, logger):
    """
    Extract Air Quality from GCP 
    target location from .env
    datetime from now + 12 hours (schedule to run at midnight, pull noon forecast)
    """
    location = {
        "latitude": cfg.LAT,
        "longitude": cfg.LON
    }
    period = {
        "startTime": (datetime.datetime.now(datetime.timezone.utc)
                      + datetime.timedelta(hours=12)
                      ).isoformat().replace("+00:00", "Z"),
        "endTime": (datetime.datetime.now(datetime.timezone.utc)
                      + datetime.timedelta(hours=24)
                      ).isoformat().replace("+00:00", "Z"),
    }
    #date_time = (
    #    datetime.datetime.now(datetime.timezone.utc)
    #    + datetime.timedelta(hours=12)
    #).isoformat().replace("+00:00", "Z")

    #extra_computations = ["POLLUTANT_ADDITIONAL_INFO"]

    request_body = {
        "location": location,
        "period": period#,
        #"dateTime": date_time,
        #"extraComputations": extra_computations
    }

    headers = {
            "Content-Type": "application/json",
        }
    logger.debug(f"Request body: {request_body}")
    r = requests.post(f"https://airquality.googleapis.com/v1/forecast:lookup?key={cfg.MAPS_KEY}", 
                      json=request_body,
                      headers=headers)
    if r.status_code != 200:
        if r.status_code == 403:
            logger.error(f"403 with key: {cfg.MAPS_KEY}")
        logger.error(f"Request failed with status code {r.status_code}: {r.text}")
    logger.debug(f"Response: {r.text}")
    return r.json()


def get_weather_data(cfg, logger):
    """
    Extract Weather Data from GCP 
    target location from .env
    datetime from now + 12 hours (schedule to run at midnight, pull noon forecast)
    """

    headers = {
            "Content-Type": "application/json",
        }
    r = requests.get(f"https://weather.googleapis.com/v1/forecast/hours:lookup?key={cfg.MAPS_KEY}&location.latitude={cfg.LAT}&location.longitude={cfg.LON}&hours=24", 
                      headers=headers)
    if r.status_code != 200:
        if r.status_code == 403:
            logger.error(f"403 with key: {cfg.MAPS_KEY}")
        logger.error(f"Request failed with status code {r.status_code}: {r.text}")
    logger.debug(f"Response: {r.text}")
    return r.json()


def get_pollen_data(cfg, logger):
    """
    Extract Pollen Data from GCP 
    target location from .env
    datetime from now + 12 hours (schedule to run at midnight, pull noon forecast)
    """

    headers = {
            "Content-Type": "application/json",
        }
    r = requests.get(f"https://pollen.googleapis.com/v1/forecast:lookup?key={cfg.MAPS_KEY}&location.longitude={cfg.LON}&location.latitude={cfg.LAT}&days=1", 
                      headers=headers)
    if r.status_code != 200:
        if r.status_code == 403:
            logger.error(f"403 with key: {cfg.MAPS_KEY}")
        logger.error(f"Request failed with status code {r.status_code}: {r.text}")
    logger.debug(f"Response: {r.text}")
    return r.json()


def app(cfg):
    logging.config.dictConfig(cfg.LOG_CONFIG)
    logger = logging.getLogger(__name__)
    air_quality_data = get_air_quality(cfg, logger)
    with open("air_quality_sample.json", "w") as f:
        json.dump(air_quality_data, f)
    # weather_data = get_weather_data(cfg, logger)
    # with open("weather_sample.json", "w") as f:
    #     json.dump(weather_data, f)
    # pollen_data = get_pollen_data(cfg, logger)
    # with open("pollen_sample.json", "w") as f:
    #    json.dump(pollen_data, f)
    logger.debug("Done...")
