from abc import abstractmethod, ABC
from typing import Any, List

import megastone as ms

from hyperstone.plugins.base import Plugin


class GenericConsts(Plugin):
    """
    Just a plugin for even below base generic consts
    """
    def _handle_interact(self, *objs: Any):
        pass


class GenericArchConsts(GenericConsts):
    @property
    @abstractmethod
    def args(self) -> List[str]:
        pass

    @property
    @abstractmethod
    def to_ms(self) -> ms.Architecture:
        pass


class Consts(GenericArchConsts):
    """
    Bare minimum consts for hyperstone
    """
    ...
