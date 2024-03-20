import operator


class LazyResolver:
    def __init__(self, subject):
        self._subject = subject
        self._actions = []

    def __add__(self, other):
        self._actions.append((operator.add, other))
        return self

    def __sub__(self, other):
        self._actions.append((operator.sub, other))
        return self

    def __mul__(self, other):
        self._actions.append((operator.mul, other))
        return self

    def __getattr__(self, item):
        self._actions.append((operator.attrgetter(item),))
        return self

    def __getitem__(self, item):
        self._actions.append((operator.getitem, item))
        return self

    def __call__(self):
        for act in self._actions:
            oper = act[0]
            params = act[1:]
            self._subject = oper(self._subject, *params)

        self._actions.clear()

        return self._subject

    def __int__(self):
        return self()
