#!/usr/bin/env python3
import logging
import logging.config
import datetime
import requests
from bs4 import BeautifulSoup
from .utils import day_of_week, get_headers, hex_to_grayscale


def get_page(target_url, pull_retry=1):
    """
    Extract content from the target URL.
    """
    retry_limit = max(1, int(pull_retry))
    retry_count = 0

    while retry_count < retry_limit:
        try:
            headers = get_headers()
            r = requests.get(target_url, headers=headers, verify=False, timeout=30)
            r.raise_for_status()
            return r.content
        except requests.RequestException as e:
            retry_count += 1
            logging.error(f"Error fetching data from {target_url}: on retry {retry_count} - {e}")
    return None


def parse_element(el):
    date = datetime.datetime.strptime(el["data-xvalue"], "%m/%d/%Y %H:%M:%S")
    return {"y": el["data-yvalue"],
            "color": hex_to_grayscale(el["fill"]),
            "day": day_of_week(date),
            "date": str(date.date())}


def extract_content(page_content):
    """
    Extract the chart bar data from the source page.
    """
    if page_content is None:
        raise ValueError("No page content was returned from the source URL.")

    soup = BeautifulSoup(page_content, features="html.parser")
    if soup.body is None:
        raise ValueError("Source page did not contain a body element.")

    chart_bars = soup.body.find_all('rect', class_='index-chart-bar')
    if not chart_bars:
        raise ValueError("Source page did not contain any index-chart-bar elements.")

    return [parse_element(bar) for bar in chart_bars]


def build_trmnl_payload(extracted_data):
    core_payload = {x:extracted_data[x] for x in range(len(extracted_data))}
    return {"merge_variables": core_payload}


def webhook_upload(target_url, data):
    """
    Send extracted data to the configured webhook URL.
    """
    try:
        response = requests.post(target_url, json=data, verify=False)
        response.raise_for_status()
        logging.debug(f"Webhook response from {target_url}: {response.status_code} - {response.text}")
        logging.info("Data successfully sent to webhook.")
    except requests.RequestException as e:
        logging.error(f"Error sending data to webhook: {e}")


def run(cfg):
    logging.config.dictConfig(cfg.LOG_CONFIG)
    logger = logging.getLogger(__name__)
    logger.info("TRMNL Agent starting up")

    pull_retry = getattr(cfg, "PULL_RETRY", None)
    if isinstance(pull_retry, (int, str)):
        page_content = get_page(cfg.SOURCE_URL, pull_retry)
    else:
        page_content = get_page(cfg.SOURCE_URL)
    if page_content is None:
        message = f"Failed to fetch source data from {cfg.SOURCE_URL}"
        logger.error(message)
        raise RuntimeError(message)

    try:
        extracted_data = extract_content(page_content)
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        logger.exception("Source data extraction failed for %s", cfg.SOURCE_URL)
        raise RuntimeError(f"Failed to extract source data from {cfg.SOURCE_URL}") from exc

    logger.info("Source Data Extracted Successfully")
    data = build_trmnl_payload(extracted_data)
    logger.debug(f"Extracted data: {data}")
    webhook_upload(cfg.WEBHOOK_URL, data)
    logger.info("Upload Completed. TRMNL Agent finished execution")
