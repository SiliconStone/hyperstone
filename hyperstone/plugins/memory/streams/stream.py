from dataclasses import dataclass
from typing import Optional

from hyperstone.emulator import HyperEmu


@dataclass
class Stream:
    @property
    def base(self) -> Optional[int]:
        return None

    @base.setter
    def base(self, value: Optional[int]):
        pass

    @staticmethod
    def raw(_: HyperEmu) -> bytes:
        return b''
