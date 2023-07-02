import os
from utils import crawl_kolekcjoner, get_google_spreadsheet, obtain_new_items, send_sms_notification
from utils import compose_notification_text, generate_google_api_credentials
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s %(asctime)s %(name)-2s %(message)s',
                    datefmt='%y-%m-%d %H:%M:%S')

# config
SCOPE = [
        'https://kolekcjoner.nbp.pl/kategoria-produktu/monety-srebrne',
        'https://kolekcjoner.nbp.pl/kategoria-produktu/nbp-banknoty-kolekcjonerskie'
        ]
RECEIVER_PHONES = os.getenv('RECEIVER_PHONES').split(';')
GSPREADSHEET_KEY = os.getenv('GSPREADSHEET_KEY')
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
WORKSHEET_NAME_SNAPSHOTS = 'snapshots'
WORKSHEET_NAME_IGNORED_ITEMS = 'ignored'
WORKSHEET_COLUMNS = ['timestamp', 'source', 'name', 'url', 'price']
NOTIFICATION_HEADER = 'NOWOŚĆ NA KOLEKCJONER NBP'
ALLOWED_NEW_ITEMS_LIMIT = 5

def main():
    items_snapshot = crawl_kolekcjoner(SCOPE)
    spreadsheet = get_google_spreadsheet(GSPREADSHEET_KEY, generate_google_api_credentials())
    ws_snapshots = spreadsheet.worksheet(WORKSHEET_NAME_SNAPSHOTS)

    ignored_item_urls = spreadsheet.worksheet(WORKSHEET_NAME_IGNORED_ITEMS).col_values(1)
    prev_item_urls = ws_snapshots.col_values(4)[1:]  # column 4 ("D") stores item url
    new_items = obtain_new_items(items_snapshot, prev_item_urls, ignored_item_urls)
    if new_items:
        new_items_count = len(new_items)
        logging.info(f'There are {new_items_count} new products!')
        if len(new_items) <= ALLOWED_NEW_ITEMS_LIMIT:
            messages = compose_notification_text(new_items, NOTIFICATION_HEADER)
            _ = send_sms_notification(messages, RECEIVER_PHONES)
        else:
            logging.info(f'Exceeded new items limit. The limit is {ALLOWED_NEW_ITEMS_LIMIT} items and number of new items is {new_items_count}.')
    else:
        logging.info('There are not any new items on NBP kolekcjoner')
    logging.info('Updating spreadsheet')
    ws_snapshots.clear()
    ws_snapshots.update('A1', [WORKSHEET_COLUMNS])
    ws_snapshots.update('A2', [list(d.get_dict().values()) for d in items_snapshot])
    logging.info('Done.')


if __name__ == '__main__':
    main()
