from abc import abstractmethod
from dataclasses import dataclass

from hyperstone.emulator import HyperEmu


@dataclass(frozen=True)
class Argument:
    @abstractmethod
    def get(self, emu: HyperEmu) -> int:
        pass

    @abstractmethod
    def set(self, emu: HyperEmu, value: int) -> None:
        pass
