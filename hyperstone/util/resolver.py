from typing import Optional, List
import operator


class LazyResolver:
    """
    An object that allows resolving other objects on demand.
    This works by queuing all actions done to an object until we need to resolve() or turn it into int(), for example
    """
    def __init__(self, subject, actions: Optional[List] = None):
        self._subject = subject
        if actions is None:
            actions = []
        self._actions = actions

    def __add__(self, other):
        return LazyResolver(self._subject, self._actions + [(operator.add, other)])

    def __radd__(self, other):
        return LazyResolver(self._subject, self._actions + [(operator.add, other)])

    def __format__(self, format_spec):
        return self.resolve().__format__(format_spec)

    def __sub__(self, other):
        return LazyResolver(self._subject, self._actions + [(operator.sub, other)])

    def __mul__(self, other):
        return LazyResolver(self._subject, self._actions + [(operator.mul, other)])

    def __rmul__(self, other):
        return LazyResolver(self._subject, self._actions + [(operator.mul, other)])

    def __getattr__(self, item):
        return LazyResolver(self._subject, self._actions + [(operator.attrgetter(item),)])

    @staticmethod
    def op_call(subject, args, kwargs):
        return subject(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        return LazyResolver(self._subject, self._actions + [(LazyResolver.op_call, args, kwargs)])

    def __getitem__(self, item):
        return LazyResolver(self._subject, self._actions + [(operator.getitem, item)])

    def resolve(self):
        subject = self._subject
        for act in self._actions:
            oper = act[0]
            params = act[1:]
            subject = oper(subject, *params)

        return subject

    def __int__(self):
        return int(self.resolve())

    def __str__(self):
        return str(self.resolve())
