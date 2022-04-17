from bs4 import BeautifulSoup
import requests
import gspread
import boto3
from datetime import datetime
import os
from ast import literal_eval

CRAWLING_SCOPE = [
        'https://kolekcjoner.nbp.pl/kategoria-produktu/monety-srebrne/',
        'https://kolekcjoner.nbp.pl/kategoria-produktu/nbp-banknoty-kolekcjonerskie/'
        ]
RECEIVER_PHONES = os.getenv('RECEIVER_PHONES').split(';')


def send_sns_sms_notification(product):
    sns = boto3.client("sns")
    message = f'''NOWY PRODUKT NA KOLEKCJONER NBP!!!\n{product['name']}\n{product['price']}\n{product['url']}'''
    for i, receiver in enumerate(RECEIVER_PHONES):
        print(f'Sending message to {i}')

        print(message)
        sns.publish(
            PhoneNumber=receiver,
            Message=message,
            MessageAttributes={'SenderID': {'StringValue': 'Numiz Monit', 'DataType': 'String'}}
        )
    print('Done')


def main():
    output = []
    ts = datetime.now().strftime('%x %X')
    for scope_url in CRAWLING_SCOPE:
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

    gc = gspread.service_account_from_dict(literal_eval(os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')))
    sh = gc.open_by_key(os.getenv('GSPREADSHEET_KEY'))
    wk = sh.sheet1
    rows = wk.get_values('D:D')  # get urls
    urls_hist = [row[0] for row in rows[1:]]
        
    notification_products = []
    for product in output:
        if product['url'] not in urls_hist:
            notification_products.append(product)

    if notification_products:
        print(f'There are {len(notification_products)} products!')
        for product in notification_products:
            send_sns_sms_notification(product)

    else:
        print('There are not new items on NBP kolekcjoner')

    print('Updating spreadsheet')
    wk.clear()
    wk.update('A1', [['timestamp', 'source', 'name', 'url', 'price']])
    wk.update('A2', [list(d.values()) for d in output])


if __name__ == '__main__':
    main()
