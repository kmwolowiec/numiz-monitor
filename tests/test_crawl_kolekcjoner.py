from utils import crawl_kolekcjoner, ScrapedItem, obtain_new_items
from utils import compose_notification_text, send_sms_notification
import pytest
from typing import Dict


def test_crawl_kolekcjoner_single_scope() -> None:
    output = crawl_kolekcjoner(['https://kolekcjoner.nbp.pl/kategoria-produktu/monety-srebrne/'])
    assert len(output) > 1


def test_crawl_kolekcjoner_multi_scope() -> None:
    test_case_scope = [
        'https://kolekcjoner.nbp.pl/kategoria-produktu/nbp-banknoty-kolekcjonerskie/',
        'https://kolekcjoner.nbp.pl/kategoria-produktu/monety-srebrne/'
    ]
    output = crawl_kolekcjoner(test_case_scope)
    assert len(output) > 2


@pytest.mark.skip(reason="not implemented")
def test_get_google_spreadsheet() -> None:
    pass


ITEM1 = ScrapedItem(timestamp='',  name='item1',  url='https://google.com', price='1', source='')
ITEM2 = ScrapedItem(timestamp='', name='item2', url='https://test1.com', price='1', source='')
ITEM3 = ScrapedItem(timestamp='', name='item3', url='https://test2.com', price='1', source='')


def test_obtain_new_items_none() -> None:
    new_snapshot = [ITEM1, ITEM2, ITEM3]
    previous_snapshot = ['https://google.com', 'https://test1.com', 'https://test2.com']
    ignored_items = []
    new_items = obtain_new_items(new_snapshot, previous_snapshot, ignored_items)
    assert new_items == list()


def test_obtain_new_items_true() -> None:
    new_snapshot = [ITEM1, ITEM2, ITEM3]
    previous_snapshot = ['https://google.com']
    ignored_items = []
    new_items = obtain_new_items(new_snapshot, previous_snapshot, ignored_items)
    assert new_items == [ITEM2, ITEM3]


def test_obtain_new_items_true_ignored() -> None:
    new_snapshot = [ITEM1, ITEM2, ITEM3]
    previous_snapshot = ['https://google.com']
    ignored_items = ['https://test1.com']
    new_items = obtain_new_items(new_snapshot, previous_snapshot, ignored_items)
    assert new_items == [ITEM3]


def test_compose_notification_text() -> None:
    items = [ITEM1, ITEM2]
    header = 'TEST HEADER'
    messages = compose_notification_text(new_items=items, header=header)

    expected = []
    message = """TEST HEADER
item1
1
https://google.com

item2
1
https://test1.com
"""
    expected.append(message)
    assert messages == expected


def test_send_sms_notification() -> None:

    class SMSClientMock:
        def __init__(self):
            pass

        def publish(self, PhoneNumber: str, Message: str, MessageAttributes: dict) -> Dict:
            return dict()

    statuses = send_sms_notification(messages=['test message'], receiver_phones=['111111111'], sms_client=SMSClientMock())
    expected = [dict()]
    assert statuses == expected
