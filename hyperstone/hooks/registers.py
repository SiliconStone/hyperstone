from typing import Tuple, Optional, Callable

import inspect
import types

from hyperstone.plugins.base import Plugin
from hyperstone.plugins.consts import GenericArchConsts
from hyperstone.emulator import HyperEmu


def set_retval(emu: HyperEmu, val: int):
    emu.regs[emu.arch.retval_reg.name] = val


def ret(emu: HyperEmu, val: int):
    set_retval(emu, val)
    emu.return_from_function()


def ok(emu: HyperEmu):
    ret(emu, 0)


def args(emu: HyperEmu, values: Tuple[Optional[int], ...]):
    const = Plugin.get_loaded(GenericArchConsts, emu)
    assert len(values) <= len(const.args)

    for i, arg in enumerate(values):
        if arg is None:
            continue

        emu.regs[const.args[i]] = arg
