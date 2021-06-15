
def get_recursive_attr(obj, field, default=None, split='.'):
    "like getattr() but recursive to reated objects"
    fields = field.split(split)
    for field in fields:
        obj = getattr(obj, field, default)
    return obj


def alias(name):
    "a recursive attr property"
    def _alias(self):
        return get_recursive_attr(self, name)
    return property(_alias)


def baseline(line, **base):
    if isinstance(line, str):
        for x, y in base.items():
            if line == f'${x}':
                line = y
                break
            if line.startswith(f'${x}.'):
                line = get_recursive_attr(y, line.strip(f'${x}.'))
                break
    return line


def between(value, interval, cast=int):
    """
    value=5, interval='3..8'  -->  3 <= 5 < 8
    """
    try:
        if interval.isdigit():
            return value == int(interval)
        else:
            a, b = interval.split('..')
            a = cast(a) if a else value
            b = cast(b) if b else value + 1
            return a <= value < b
    except ValueError:
        return False


def setargs(ins, **args):
    for k, v in args.items():
        if not hasattr(ins, k):
            logger.warning(f"overwriters.setargs: '{k}' not in {type(ins)} object")
        setattr(ins, k, v)


def boolean(x):
    "boolean(str(bool)) --> bool"
    if x not in ['True', 'False']:
        raise ValueError
    return x == 'True'


def valuate(x):
    "valuate(str(value)) --> value"
    x = x.strip()
    for cast in [int, float, boolean, str]:
        try:
            x = cast(x)
        except ValueError:
            continue
        return x

"""
# given
rules = "event.condition(): b=3"
condition = lambda x: x.a == 1
r = Mock(a=1)
w = [Mock(b=2)]

# when
Overwriter.trigger(rules, 'event', r, w)

# then
assert y.b == 3
"""

class Overwriter():
    CALLBACKS = {}

    OP = {
        '|@': lambda x, y, *z: x.append(Overwriter.CALLBACKS.get(y)(*z)),
        '=@': lambda x, y, *z: Overwriter.CALLBACKS.get(y)(*z),
        '+@': lambda x, y, *z: x + Overwriter.CALLBACKS.get(y)(*z),
        '-@': lambda x, y, *z: x - Overwriter.CALLBACKS.get(y)(*z),
        '*@': lambda x, y, *z: round(x * Overwriter.CALLBACKS.get(y)(*z), 3),
        '<@': lambda x, y, *z: min(x, Overwriter.CALLBACKS.get(y)(*z)),
        '>@': lambda x, y, *z: max(x, Overwriter.CALLBACKS.get(y)(*z)),

        '|': lambda x, *y: x.extend(y) or x,
        '=': lambda x, y: y,
        '+': lambda x, y: x + y,
        '-': lambda x, y: x - y,
        '*': lambda x, y: round(x * y, 3),
        '<': lambda x, *y: min(x, *y),
        '>': lambda x, *y: max(x, *y),
    }

    def __init__(self, text):
        self.text = text
        item = self._parse(text)
        self.when = item['when'] or ''
        self.what = item['what'] or 'cmp'
        self.args = item['args'] or []
        self.kwargs = item['kwargs'] or {}
        self.ops = item['ops'] or {}

    def __str__(self):
        return self.text

    @property
    def callback(self):
        return self.CALLBACKS[self.what]

    @classmethod
    def add(cls, foo, name=None):
        name = name or foo.__name__
        Overwriter.CALLBACKS[name] = foo
        return foo

    @classmethod
    def trigger(cls, text='', event='', readable=None, writables=None):
        writables = writables or [readable]
        writers = [Overwriter(s.strip()) for s in text.split('\n') if s.strip()]
        writers = [w for w in writers if w.when == event]
        response = []
        for w in writers:
            if w.ask(readable):
                w.apply(writables, readable)
                response.append(str(w))
        return response

    @classmethod
    def _parse(cls, s):
        """Takes an string in format 'when.what(1,a=2): b=3, c+4, d-5, e*6, f|7, g<8, h>9'
        returns dict(id, when, what, args=[], kwargs={}, values={}, add={}), mul={}, append={})"""
        try:
            x1, x2 = s.split(':')
        except ValueError:
            raise ValueError(f'Not enough values to unpack on "{s}".split(":")')
        condition, arguments = x1.split('(')
        what, when, *trash = condition.split('.')[::-1] + ['', '']
        arguments = [arg for arg in arguments.strip(')').split(',') if arg not in (None, '')]
        d = {
            'when': when.strip(), 'what': what.strip(),
            'args': [], 'kwargs': {},
            'ops': {},
        }

        for x in arguments:
            if '=' in x:
                a, b = x.split('=')
                d['kwargs'][a.strip()] = valuate(b)
            else:
                d['args'].append(valuate(x))
        if x2:
            q = x2.split(',')
            for x in q:
                x = x.strip()
                for op in cls.OP:
                    if op in x:
                        a, b = x.split(op)
                        d['ops'].setdefault(op, {})[a] = map(valuate, b.split())
                        break
        return d

    def ask(self, base):
        if self.callback is None:
            return None
        return self.callback(base, *self.args, **self.kwargs)

    def apply(self, writables, base):
        for op, values in self.ops.items():
            operation = self.OP[op]
            for attr, value in values.items():
                for w in writables:
                    if hasattr(w, attr):
                        old_value = getattr(w, attr)
                        value = [baseline(x, b=base, w=w, x=old_value) for x in value]
                        new_value = operation(old_value, *value)
                        try:
                            setattr(w, attr, new_value)
                        except AttributeError:
                            raise AttributeError(f'({attr}={new_value}) on "{self.text}"')
                        break
                else:
                    logger.warning(f"Missing attribute {attr} on {writables}")


_OP = {
    'lt': lambda x, y: x < y,
    'lte': lambda x, y: x <= y,
    'gt': lambda x, y: x > y,
    'gte': lambda x, y: x >= y,
    'neq': lambda x, y: x != y,
    'in': lambda x, y: x in y,
    'notin': lambda x, y: x not in y,
    'eq': lambda x, y: x == y,
    'has': lambda x, y: y in x,
    'hasnt': lambda x, y: y not in x,
    'btw': lambda x, y: between(x, y),
}

def f_cmp(x_, **attrs):
    "e.g.: cpm_value(pa, value__lte=5) --> pa.value <= 5"
    b = True
    try:
        for attr, value2 in attrs.items():
            s = attr.split('.')
            if len(s) > 1 and s[-1] in _OP:
                op = s[-1]
                cmp = _OP[op]
                value1 = get_recursive_attr(x_, attr.rstrip(f'{op}').strip('.'))
                b = b and cmp(value1, value2)
            else:
                value1 = get_recursive_attr(x_, attr)
                b = b and value1 == value2
    except (AttributeError, TypeError) as e:
        print('Error on cmp', x_, attrs, e)
        return False
    return b


def f_between(x_, attr, interval):
    value = get_recursive_attr(x_, attr)
    return between(value, interval)


def f_not(x_, function, *args, **kwargs):
    return not Overwriter.CALLBACKS[function](x_, *args, **kwargs)

Overwriter.add(f_cmp, 'cmp')
Overwriter.add(f_not, 'not')
Overwriter.add(f_between, 'between')