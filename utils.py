from bs4 import BeautifulSoup
import gspread
import boto3

from datetime import datetime
from ast import literal_eval
from time import sleep
from pytz import timezone
import requests
import random
import sys
from typing import List
from dataclasses import dataclass
import logging
import os

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s %(asctime)s %(name)-2s %(message)s',
                    datefmt='%y-%m-%d %H:%M:%S')

SMS_PUBLISH_BYTES_LIMIT = 1334


@dataclass
class ScrapedItem:
    """Base representation of numismatic product information."""
    timestamp: str
    source: str
    name: str
    url: str
    price: str

    def get_dict(self):
        return self.__dict__


def crawl_kolekcjoner(urls: List) -> List[ScrapedItem]:
    """Crawl NBP and collect coins and banknotes information.
    :param urls: scope for BeautifulSoup for scraping. Scrape items that are listed in these urls.
    :return a list of numismatic items currently visible on the website."""
    scraped_items = []
    ts = datetime.now(timezone('Europe/Warsaw')).strftime('%x %X')
    sleep(random.randint(0, 5))  # silly method of preventing being detected as a scraper
    for scope_url in urls:
        while True:
            logging.info(f'------ {scope_url} -------')
            for i in range(5):
                res = requests.get(url=scope_url)
                logging.info(f'Status code: {res.status_code}')
                if res.ok:
                    break
                sleep(random.randint(0, 5))

            soup = BeautifulSoup(res.content, 'html.parser')
            divs = soup.find_all('div', 'box-text box-text-products')

            for div in divs:
                name = div.find('a', 'woocommerce-LoopProduct-link').text
                url = div.find('a', 'woocommerce-LoopProduct-link').get('href')
                price = div.find('span', 'woocommerce-Price-amount amount').text
                source = scope_url.split('/')[4]  # coins or banknotes
                item = ScrapedItem(timestamp=ts, source=source, name=name, url=url, price=price)
                scraped_items.append(item)
                logging.info(f'''{item.timestamp}, {item.name}, {item.url}, {item.price}\n''')
            next_page = soup.find('a', 'next page-number')
            if next_page:
                scope_url = next_page.get('href')
            else:
                break
    logging.info(f'Obtained {len(scraped_items)} items.')
    return scraped_items


def get_google_spreadsheet(spreadsheet_key: str, service_account_json: dict) -> gspread.spreadsheet.Spreadsheet:
    """Get google spreadsheet it's key ans using provided service account credentials.

    :param spreadsheet_key: part of URL standing for a spreadsheet
    :param service_account_json: json service account credentials
    :return spreadsheet object"""
    gc = gspread.service_account_from_dict(service_account_json)
    spreadsheet = gc.open_by_key(spreadsheet_key)
    return spreadsheet


def obtain_new_items(new_snapshot: List[ScrapedItem], previous_snapshot: List[str], ignored_items: List[str]) -> List[ScrapedItem]:
    """Compare new scraping snapshot and a previous one in order to identify the items incremental.
    Don't keep items existing in ignored items list. The list contains constantly disappearing and returning products.
    Such products are problematic because they trigger many notifications causing spam.

    :param new_snapshot: a list of items that are suppose to appear on the website the first time or
        returned to the website. These items are going to be checked against `previous_snapshot` and `ignored_items`
    :param previous_snapshot: Reference for `new_snapshot`. List of item urls from previous snapshot.
    :param ignored_items: List of item urls that returns to the website frequently.
        Some items constantly disappear and get back to the website what cause notification spamming."""

    new_items = []
    for item in new_snapshot:
        if item.url not in previous_snapshot and item.url not in ignored_items:
            new_items.append(item)
    return new_items


def compose_notification_text(new_items: List[ScrapedItem], header: str) -> List[str]:
    """Create notification text to be sent using SNS SMS.
    The notification schema:
    <HEADER>
    <NAME>
    <PRICE>
    <URL>

    :param new_items: item information that is going to be included in notification text
    :param header: a notification header appearing at the beginning of the notification
    :return: list of notifications; each notification have to be sent separately
    """
    messages = []
    message = ''

    # Add header to the first message:
    message += header
    for item in new_items:
        new_item_desc = f"\n{item.name}\n{item.price}\n{item.url}\n"

        # Don't let the message size exceed the max size of SMS publish bytes limit set for AWS SNS:
        # If the size is exceeded, the message is not delivered.
        # The workaround is to split the notification text into multiple parts and send multiple messages.
        if sys.getsizeof(message) + sys.getsizeof(new_item_desc) >= SMS_PUBLISH_BYTES_LIMIT:
            messages.append(message)
            message = ''
        message += new_item_desc
    if message != '':
        messages.append(message)
    return messages


def send_sms_notification(messages: List[str], receiver_phones: List[str], sms_client=boto3.client('sns')) -> List:
    """Connect to AWS SNS service and send `messages` to receivers (`receiver_phones`)."""
    logging.info(f'Number of messages to send: {len(messages)}')
    statuses = []
    for i, receiver in enumerate(receiver_phones):
        logging.info(f'Sending messages to {i}')
        for message in messages:
            logging.info(message)
            status = sms_client.publish(
                PhoneNumber=receiver,
                Message=message,
                MessageAttributes={'SenderID': {'StringValue': 'NumizMonit', 'DataType': 'String'}}
            )
            statuses.append(status)
            logging.info(status)
    logging.info('Done')
    return statuses


def generate_google_api_credentials():
    credentials = {
        "type": "service_account",
        "project_id": os.getenv('GOOGLE_PROJECT_ID'),
        "private_key_id": os.getenv('GOOGLE_PRIVATE_KEY_ID'),
        "private_key": os.getenv('GOOGLE_PRIVATE_KEY'),
        "client_email": os.getenv('GOOGLE_CLIENT_EMAIL'),
        "client_id": os.getenv('GOOGLE_CLIENT_ID'),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.getenv('GOOGLE_CLIENT_X509_CERT_URL')
    }
    return credentials
