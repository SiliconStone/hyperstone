"""
This module is a legacy implementation and may be removed in a future release.
Please do not use this.
Use calls instead, it's much better.
Please
I'm begging you

See Also:
    `hyperstone.calls`
"""

from abc import abstractmethod
from typing import Any, List, Type

import megastone as ms

from hyperstone.plugins.base import Plugin


class GenericConsts(Plugin):
    """
    Just a plugin for even below base generic consts
    """
    def _handle(self, obj: Any):
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

    @property
    def plugin_identity(self) -> List[Type]:
        return [type(self), GenericArchConsts, Plugin]
    ...


class ARMConsts(Consts):
    @property
    def args(self) -> List[str]:
        return ['r0', 'r1', 'r2', 'r3']

    @property
    def to_ms(self) -> ms.Architecture:
        return ms.ARCH_ARM
