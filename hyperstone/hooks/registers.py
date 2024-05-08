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


def eabi(emu: HyperEmu, func: Callable[[HyperEmu, ...], None], *func_args,
         respect_defaults: bool = True, **func_kwargs):
    const_plugin = Plugin.get_loaded(GenericArchConsts, emu)

    func_call = func
    if not inspect.isroutine(func_call):
        # Usually means __call__ override.
        # Since argument is Callable, it means we have __call__
        # noinspection PyUnresolvedReferences
        func_call = func_call.__call__

    func_code: types.CodeType = func_call.__code__

    positional_count = func_code.co_argcount + func_code.co_posonlyargcount - 1  # 1 for emu

    if respect_defaults and func_call.__defaults__ is not None:
        positional_count -= len(func_call.__defaults__)

    userargs_compensate = len(func_args)
    arg_pull_amount = positional_count - userargs_compensate

    assert userargs_compensate <= positional_count
    assert len(const_plugin.args) >= arg_pull_amount

    reg_args = []
    for i in range(arg_pull_amount):
        reg_args.append(emu.regs[const_plugin.args[i]])

    assert len(reg_args) + len(func_args) == positional_count

    func(emu, *reg_args, *func_args, **func_kwargs)
