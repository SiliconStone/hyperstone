from typing import List, Optional

from hyperstone.plugins.base import Plugin
from hyperstone.plugins.consts import GenericArchConsts
from hyperstone.emulator import HyperEmu
from hyperstone.exceptions import HSPluginNotFoundError

def ret(emu: HyperEmu, val: int):
    emu.regs[emu.arch.retval_reg.name] = val


def ok(emu: HyperEmu):
    ret(emu, 0)


def args(emu: HyperEmu, values: List[Optional[int]]):
    const = Plugin.get_loaded(GenericArchConsts, emu)
    assert len(values) <= len(const.args)

    for i, arg in enumerate(values):
        if arg is None:
            continue

        emu.regs[const.args[i]] = arg

