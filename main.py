import os
from utils import crawl_kolekcjoner, get_google_sheet, obtain_new_items, send_sns_sms_notification
from utils import compose_notification_text

# config
CRAWLING_SCOPE = [
        'https://kolekcjoner.nbp.pl/kategoria-produktu/monety-srebrne/',
        'https://kolekcjoner.nbp.pl/kategoria-produktu/nbp-banknoty-kolekcjonerskie/'
        ]
RECEIVER_PHONES = os.getenv('RECEIVER_PHONES').split(';')
GSPREADSHEET_KEY = os.getenv('GSPREADSHEET_KEY')
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
WORKSHEET_COLUMNS = ['timestamp', 'source', 'name', 'url', 'price']


def main():
    numizmatic_items_snapshot = crawl_kolekcjoner(CRAWLING_SCOPE)
    wk = get_google_sheet(GSPREADSHEET_KEY, GOOGLE_SERVICE_ACCOUNT_JSON)
    rows = wk.get_values('D:D')  # column D - item url
    numizmatic_item_urls_previous_snapshot = [row[0] for row in rows[1:]]
    new_items = obtain_new_items(numizmatic_items_snapshot, numizmatic_item_urls_previous_snapshot)

    if new_items:
        print(f'There are {len(new_items)} products!')
        messages = compose_notification_text(new_items)
        send_sns_sms_notification(messages, RECEIVER_PHONES)
    else:
        print('There are not new items on NBP kolekcjoner')
    print('Updating spreadsheet')
    wk.clear()
    wk.update('A1', [WORKSHEET_COLUMNS])
    wk.update('A2', [list(d.values()) for d in numizmatic_items_snapshot])


if __name__ == '__main__':
    main()
