import os
from utils import crawl_kolekcjoner, get_google_sheet, obtain_new_items, send_sns_sms_notification
from utils import compose_notification_text

# config
SCOPE = [
        'https://kolekcjoner.nbp.pl/kategoria-produktu/monety-srebrne/',
        'https://kolekcjoner.nbp.pl/kategoria-produktu/nbp-banknoty-kolekcjonerskie/'
        ]
RECEIVER_PHONES = os.getenv('RECEIVER_PHONES').split(';')
GSPREADSHEET_KEY = os.getenv('GSPREADSHEET_KEY')
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
WORKSHEET_COLUMNS = ['timestamp', 'source', 'name', 'url', 'price']
IGNORE_ITEM_LIST = [
    'https://kolekcjoner.nbp.pl/produkt/10-zl-wielcy-polscy-ekonomisci-jan-stanislaw-lewinski/',
    'https://kolekcjoner.nbp.pl/produkt/10-zl-wielcy-polscy-ekonomisci-leon-biegeleisen/',
    'https://kolekcjoner.nbp.pl/produkt/10-zl-stulecie-odzyskania-przez-polske-niepodleglosci-ignacy-daszynski/',
    'https://kolekcjoner.nbp.pl/produkt/10-zl-wielcy-polscy-ekonomisci-tadeusz-brzeski/',
    'https://kolekcjoner.nbp.pl/produkt/20-zl-wielkie-aktorki-gabriela-zapolska/',
    'https://kolekcjoner.nbp.pl/produkt/10-zl-wielcy-polscy-ekonomisci-adam-krzyzanowski-2/',
    'https://kolekcjoner.nbp.pl/produkt/10-zl-wielcy-polscy-ekonomisci-ferdynand-zweig/',
    'https://kolekcjoner.nbp.pl/produkt/10-zl-wielcy-polscy-ekonomisci-adam-heydel/',
    'https://kolekcjoner.nbp.pl/produkt/10-zl-75-rocznica-zaglady-romow-i-sinti/',
    'https://kolekcjoner.nbp.pl/produkt/10-zl-my-polacy-dumni-i-wolni-1918-2018/',
    'https://kolekcjoner.nbp.pl/produkt/10-zl-centrum-pieniadza-narodowego-banku-polskiego-im-slawomira-s-skrzypka/',
    'https://kolekcjoner.nbp.pl/produkt/50-zl-jan-pawel-ii/'
]


def main():
    snapshot = crawl_kolekcjoner(SCOPE)
    wk = get_google_sheet(GSPREADSHEET_KEY, GOOGLE_SERVICE_ACCOUNT_JSON)
    rows = wk.get_values('D:D')  # column D - item url
    hist_snapshot = [row[0] for row in rows[1:]]
    new_items = obtain_new_items(snapshot, hist_snapshot)
    new_items = [item for item in new_items if item['url'] not in IGNORE_ITEM_LIST]

    if new_items:
        print(f'There are {len(new_items)} products!')
        messages = compose_notification_text(new_items)
        send_sns_sms_notification(messages, RECEIVER_PHONES)
    else:
        print('There are not new items on NBP kolekcjoner')
    print('Updating spreadsheet')
    wk.clear()
    wk.update('A1', [WORKSHEET_COLUMNS])
    wk.update('A2', [list(d.values()) for d in snapshot])
    print('Done.')


if __name__ == '__main__':
    main()
