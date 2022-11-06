import os
from utils import crawl_kolekcjoner, get_google_spreadsheet, obtain_new_items, send_sns_sms_notification
from utils import compose_notification_text

# config
SCOPE = [
        'https://kolekcjoner.nbp.pl/kategoria-produktu/monety-srebrne/',
        'https://kolekcjoner.nbp.pl/kategoria-produktu/nbp-banknoty-kolekcjonerskie/'
        ]
RECEIVER_PHONES = os.getenv('RECEIVER_PHONES').split(';')
GSPREADSHEET_KEY = os.getenv('GSPREADSHEET_KEY')
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
WORKSHEET_NAME_SNAPSHOTS = 'snapshots'
WORKSHEET_NAME_IGNORED_ITEMS = 'ignored'
WORKSHEET_COLUMNS = ['timestamp', 'source', 'name', 'url', 'price']
NOTIFICATION_HEADER = 'NOWOŚĆ NA KOLEKCJONER NBP'


def main():
    items_snapshot = crawl_kolekcjoner(SCOPE)
    spreadsheet = get_google_spreadsheet(GSPREADSHEET_KEY, GOOGLE_SERVICE_ACCOUNT_JSON)
    ws_snapshots = spreadsheet.worksheet(WORKSHEET_NAME_SNAPSHOTS)

    ignored_item_urls = spreadsheet.worksheet(WORKSHEET_NAME_IGNORED_ITEMS).col_values(1)
    prev_item_urls = ws_snapshots.col_values(4)[1:]  # column 4 ("D") stores item url
    new_items = obtain_new_items(items_snapshot, prev_item_urls, ignored_item_urls)

    if new_items:
        print(f'There are {len(new_items)} products!')
        messages = compose_notification_text(new_items, NOTIFICATION_HEADER)
        send_sns_sms_notification(messages, RECEIVER_PHONES)
    else:
        print('There are not any new items on NBP kolekcjoner')
    print('Updating spreadsheet')
    ws_snapshots.clear()
    ws_snapshots.update('A1', [WORKSHEET_COLUMNS])
    ws_snapshots.update('A2', [list(d.get_dict().values()) for d in items_snapshot])
    print('Done.')


if __name__ == '__main__':
    main()
