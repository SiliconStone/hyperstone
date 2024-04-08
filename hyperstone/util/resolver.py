from typing import Optional, List
import operator


class LazyResolver:
    def __init__(self, subject, actions: Optional[List] = None):
        self._subject = subject
        if actions is None:
            actions = []
        self._actions = actions

    def __add__(self, other):
        return LazyResolver(self._subject, self._actions + [(operator.add, other)])

    def __sub__(self, other):
        return LazyResolver(self._subject, self._actions + [(operator.sub, other)])

    def __mul__(self, other):
        return LazyResolver(self._subject, self._actions + [(operator.mul, other)])

    def __getattr__(self, item):
        return LazyResolver(self._subject, self._actions + [(operator.attrgetter(item),)])

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
