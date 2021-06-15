from copy import deepcopy
import datetime


class Schema():
    "A schema is a JSON that knows how to compare himself with a similar JSON"
    def __init__(self, schema):
        self.schema = schema
    
    def __eq__(self, data):
        try:
            match_schema(data, self.schema)
        except AssertionError:
            return False
        return True

    def one(self, **kwargs):
        schema = deepcopy(self.schema)
        return Schema(update_schema(schema, kwargs))
    
    def many(self, *args, **kwargs):
        schema = deepcopy(self.schema)
        return Schema([update_schema(schema, data, **kwargs) for data in args])

    def __str__(self):
        return _schema_to_str(self.schema)

    def __repr__(self):
        return _schema_to_str(self.schema)


def _schema_to_str(data) -> str:
    if isinstance(data, dict):
        l = [f'{k}: {_schema_to_str(v)}' for k, v in data.items()]
        s = ', '.join(l)
        return '{' + s + '}'
    elif isinstance(data, list):
        l = [_schema_to_str(v) for k, v in data]
        s = ', '.join(l)
        return '[' + s + ']'
    elif isinstance(data, type):
        return data.__name__
    return repr(data)


def update_schema(schema, data, more_data=None):
    more_data = more_data or {}
    data.update(more_data)
    for key in data:
        value = data[key]
        subkeys = key.split('__')
        base = schema
        for k in subkeys[:-1]:
            if k.isdigit():
                k = int(k)
                base = base[k]
            else:
                base = base.setdefault(k, {})
        k = subkeys[-1]
        if k.isdigit():
            k = int(k)
        base[k] = value
    return schema


def is_isoformat(value, type):
    if not isinstance(value, str):
        return False
    try:
        type.fromisoformat(value.strip('Z'))
    except ValueError:
        return False
    return True


def match_schema(got, want):
    if want in [int, str, float, bool, list, dict, object]:
        return isinstance(got, want)
    if want in [datetime.date, datetime.datetime]:
        return is_isoformat(got, want)
    elif isinstance(want, list):
        for i, item in enumerate(want):
            if not match_schema(got[i], item):
                return False
        return True
    elif isinstance(want, dict):
        for key in want:
            if key not in got:
                return False
            if not match_schema(got[key], want[key]):
                return False
        return True
    elif isinstance(want, tuple):
        for item in want:
            if match_schema(got, item):
                return True
        return False
    else:
        return got == want
