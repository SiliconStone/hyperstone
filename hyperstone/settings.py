from .plugins import Plugin
from typing import Type, Union


class MetaSetting(type):
    def __iter__(cls):
        # This is done to allow pushing imported plugins while running
        items = list(vars(cls))
        for item in items:
            if item.startswith('_'):
                continue

            obj = getattr(cls, item)
            if not isinstance(obj, Plugin):
                continue

            yield obj

    def __repr__(cls):
        out = f'{cls.__name__}:\n'

        for item in vars(cls):
            if item.startswith('_'):
                continue
            out += f'\t{item}: {getattr(cls, item)}\n'

        return out


class Settings(metaclass=MetaSetting):
    pass


SettingsType = Union[Type[Settings], Settings]
