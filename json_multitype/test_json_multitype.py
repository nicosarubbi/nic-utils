import datetime
import decimal
import json

from unittest import TestCase
from .json_multitype import MultitypeEncoder, MultitypeDecoder


class MultitypeJsonEncoders(TestCase):
    def test_date(self):
        data = {
            "aDate": datetime.date(2021, 12, 31),
            "aString": "2021-12-31",
            "aList": [1, 2.3, "4", {}, datetime.date(2021, 12, 31)],
            "anObject": {
                "otherDate": datetime.date(2021, 12, 31),
            },
        }
        encoded_data = json.dumps(data, cls=MultitypeEncoder)
        decoded_data = json.loads(encoded_data, cls=MultitypeDecoder)
        self.assertEqual(data, decoded_data)

    def test_datetime(self):
        data = {
            "aDatetime": datetime.datetime(2021, 12, 31, 12, 59),
            "aString": "2021-12-31",
            "aList": [1, 2.3, "4", {}, datetime.datetime(2021, 12, 31, 11, 58)],
            "anObject": {
                "otherDatetime": datetime.datetime(2021, 12, 31, 10, 57),
            },
        }
        encoded_data = json.dumps(data, cls=MultitypeEncoder)
        decoded_data = json.loads(encoded_data, cls=MultitypeDecoder)
        self.assertEqual(data, decoded_data)

    def test_decimal(self):
        data = {
            "aDecimal": decimal.Decimal("3.1415"),
            "aString": "2021-12-31",
            "aList": [1, 2.3, "4", {}, decimal.Decimal("3.1415")],
            "anObject": {
                "otherDecimal": decimal.Decimal("3.1415"),
            },
        }
        encoded_data = json.dumps(data, cls=MultitypeEncoder)
        decoded_data = json.loads(encoded_data, cls=MultitypeDecoder)
        self.assertEqual(data, decoded_data)
