from dataclasses import dataclass, field
from typing import Optional

from hyperstone.emulator import HyperEmu


@dataclass
class Stream:

    _base: Optional[int] = field(init=False, repr=False, default=None)
    @property
    def base(self) -> Optional[int]:
        return self._base

    @base.setter
    def base(self, value: Optional[int]):
        self._base = value

    @staticmethod
    def raw(_: HyperEmu) -> bytes:
        return b''
