import datetime
import decimal
import json


class JsonCoding:
    KEY_PREFIX = '_{}'

    class DecodingError(Exception):
        pass

    def __init__(self, key: str, type, encoder, decoder):
        self.key = self.KEY_PREFIX.format(key)
        self.type = type
        self.encoder = encoder
        self.decoder = decoder

    def its_my_type(self, x) -> bool:
        return isinstance(x, self.type)

    def to_json(self, obj) -> dict:
        return {self.key: self.encoder(obj)}

    @classmethod
    def to_python(cls, obj):
        if len(obj) != 1:
            return obj
        for x in cls.coders():
            if x.key in obj:
                return x.decoder(obj[x.key])
        return obj

    @classmethod
    def coders(cls):
        return [
            cls(
                key='datetime',
                type=datetime.datetime,
                encoder=lambda x: x.isoformat(),
                decoder=datetime.datetime.fromisoformat,
            ),
            cls(
                key='date',
                type=datetime.date,
                encoder=lambda x: x.isoformat(),
                decoder=datetime.date.fromisoformat,
            ),
            cls(
                key='decimal',
                type=decimal.Decimal,
                encoder=str,
                decoder=decimal.Decimal,
            ),
        ]


class MultitypeEncoder(json.JSONEncoder):
    def default(self, obj):
        for coder in JsonCoding.coders():
            if coder.its_my_type(obj):
                return coder.to_json(obj)
        return super().default(obj)


class MultitypeDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, object_hook=JsonCoding.to_python, **kwargs)
