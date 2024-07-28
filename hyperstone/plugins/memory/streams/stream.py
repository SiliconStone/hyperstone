from dataclasses import dataclass, field
from typing import Optional

from hyperstone.emulator import HyperEmu


@dataclass
class Stream:
    """
    Represents some data in some form

    Attributes:
        _base: The base address of the stream (if applicable), may be set via the `base` property

    Notes:
        This is the most abstract form of a stream, it should not be used directly. It represents no data.
    """
    _base: Optional[int] = field(init=False, repr=False, default=None)

    @property
    def base(self) -> Optional[int]:
        """The base address of the stream."""
        return self._base

    @base.setter
    def base(self, value: Optional[int]):
        self._base = value

    @staticmethod
    def raw(_: HyperEmu) -> bytes:
        """The stream as a sequence of bytes."""
        return b''
