from bs4 import BeautifulSoup
import gspread
import boto3

from datetime import datetime
from ast import literal_eval
from time import sleep
import requests
import random

def crawl_kolekcjoner(urls):
    '''Crawl through NBP'''
    output = []
    ts = datetime.now().strftime('%x %X')
    sleep(random.randint(0, 10))
    for scope_url in urls:
        print(f'------ {scope_url} -------')
        req = requests.get(scope_url)
        soup = BeautifulSoup(req.content, 'html.parser')
        divs = soup.find_all('div', 'box-text box-text-products')

        for div in divs:
            name = div.find('a', 'woocommerce-LoopProduct-link').text
            url = div.find('a', 'woocommerce-LoopProduct-link').get('href')
            price = div.find('span', 'woocommerce-Price-amount amount').text
            product_data = {
                'timestamp': ts,
                'source': scope_url.split('/')[-2],
                'name': name,
                'url': url,
                'price': price
            }
            output.append(product_data)
            print(f'''{ts}, {name}, {url}, {price}\n''')
    return output


def get_google_sheet(gsheet_key, service_account_json_string):
    gc = gspread.service_account_from_dict(literal_eval(service_account_json_string))
    sh = gc.open_by_key(gsheet_key)
    wk = sh.sheet1
    return wk


def obtain_new_items(new_snapshot, previous_snapshot):
    new_items = []
    for item in new_snapshot:
        if item['url'] not in previous_snapshot:
            new_items.append(item)
    return new_items


def validate_keys(item):
    key_schema = ['name', 'price', 'url']
    for key in key_schema:
        if key not in item.keys():
            raise KeyError(f"'{key}' not found in product description.")


def compose_notification_text(products):

    if not products:
        return ''
    message = ''
    header = 'NOWOŚĆ NA KOLEKCJONER NBP'
    message += header
    for product in products:
        validate_keys(product)
        message += f"\n{product['name']}\n{product['price']}\n{product['url']}\n"
    return message


def send_sns_sms_notification(message, receiver_phones):
    sns = boto3.client("sns")
    for i, receiver in enumerate(receiver_phones):
        print(f'Sending message to {i}')
        print(message)
        sns.publish(
            PhoneNumber=receiver,
            Message=message,
            MessageAttributes={'SenderID': {'StringValue': 'NumizMonit', 'DataType': 'String'}}
        )
    print('Done')

