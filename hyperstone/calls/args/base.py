from abc import abstractmethod
from dataclasses import dataclass

from hyperstone.emulator import HyperEmu


@dataclass(frozen=True)
class Argument:

    @property
    def is_reversed(self) -> bool:
        return False

    @property
    def needs_cleanup(self) -> bool:
        return False

    @abstractmethod
    def get(self, emu: HyperEmu) -> int:
        pass

    @abstractmethod
    def set(self, emu: HyperEmu, value: int) -> None:
        pass

    def cleanup(self, emu: HyperEmu) -> None:
        pass
