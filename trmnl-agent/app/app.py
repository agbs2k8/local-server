#!/usr/bin/env python3
import logging
import datetime
import requests
from bs4 import BeautifulSoup
from .utils import day_of_week, get_headers, hex_to_grayscale


def get_page(target_url):
    """
    Extract content from the target URL.
    """
    try:
        headers = get_headers()
        r = requests.get(target_url, headers=headers, verify=False)
        r.raise_for_status()
        return r.content
    except requests.RequestException as e:
        logging.error(f"Error fetching data from {target_url}: {e}")
        return None


def parse_element(el):
    date = datetime.datetime.strptime(el["data-xvalue"], "%m/%d/%Y %H:%M:%S")
    return {"y": el["data-yvalue"],
            "color": hex_to_grayscale(el["fill"]),
            "day": day_of_week(date)}


def extract_content(page_content):
    """
    Placeholder function to extract relevant data from the page content.
    """
    soup = BeautifulSoup(page_content, features="html.parser")
    return [parse_element(x) for x in soup.body.find_all('rect', class_='index-chart-bar')]


def build_trmnl_payload(extracted_data):
    core_payload = {x:extracted_data[x] for x in range(len(extracted_data))}
    return {"merge_variables": core_payload}
    return payload


def webhook_upload(target_url, data):
    """
    Send extracted data to the configured webhook URL.
    """
    try:
        response = requests.post(target_url, json=data)
        response.raise_for_status()
        logging.info("Data successfully sent to webhook.")
    except requests.RequestException as e:
        logging.error(f"Error sending data to webhook: {e}")


def run(cfg):
    logging.basicConfig(filename=f"{cfg.APP_NAME}.log", level=cfg.LOG_LEVEL)
    logger = logging.getLogger(__name__)
    logger.info("TRMNL Agent starting up")
    data = build_trmnl_payload(extract_content(get_page(cfg.SOURCE_URL)))
    logger.info("Source Data Extracted Successfully")
    logger.debug(f"Extracted data: {data}")
    webhook_upload(cfg.WEBHOOK_URL, data)
    logger.info("Upload Completed. TRMNL Agent finished execution")
