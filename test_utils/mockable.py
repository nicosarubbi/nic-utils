import importlib
from contextlib import ContextDecorator
from django.conf import settings

## add those to settings.py
##
## MOCKABLE_NAMES = {
##     "MockableClassName": {
##         "test": 'path.to.some.ServiceMockError',
##         "development": 'path.to.some.ServiceMockOk',
##         # "production": 'please.dont.mock.Me',
##     },
## }
## ENVIRONMENT = "local"


class Mockable:
    """Abstract class for when we need to mock something in test envinronments.
    When the class is instanciated, if settings say so, it shall return a mock instead.
    """

    __unmocked = []

    def __new__(cls, *args, **kwargs):
        "returns an instance... probably."
        mock = cls.__get_mock()
        return object.__new__(mock, *args, **kwargs)

    @classmethod
    def __get_mock(cls):
        'returns the mocked class if it should'
        if cls.__name__ in cls.__unmocked:
            return cls
        full_path = settings.MOCKABLE_NAMES.get(cls.__name__, {}).get(settings.ENVIRONMENT, None)
        if full_path is None:
            return cls
        return cls.__get_module(full_path)

    @classmethod
    def __get_module(cls, full_path: str):
        'get a module from full_path'
        path = full_path.split('.')
        module = importlib.import_module(".".join(path[:-1]))
        return getattr(module, path[-1])

    @classmethod
    def get_unmocked(cls, *args, **kwargs):
        'gets an instance of this classs, ignoring mocks'
        with unmock(cls):
            return cls(*args, **kwargs)

    @classmethod
    def unmock(cls):
        "Returns the 'unmock' decorator for this class"
        return unmock(cls)


class unmock(ContextDecorator):
    """Decorator and context manager for unmocking a Mocked class.
    Use this if settings says to mock something, but you really need the real one."""

    def __init__(self, cls):
        if issubclass(cls, Mockable):
            self.class_name = cls.__name__
        elif isinstance(cls, str):
            self.class_name = cls
        else:
            raise ValueError("cls param should be a Mockable subclass or string value.")

    def __enter__(self):
        Mockable.__unmocked.append(self.class_name)
        return self

    def __exit__(self):
        Mockable.__unmocked.remove(self.class_name)
        return False
