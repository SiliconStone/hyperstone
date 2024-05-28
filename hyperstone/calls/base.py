from abc import abstractmethod
from typing import Callable, Any, Iterator, Generator, Tuple, Dict
import inspect
import types

from hyperstone.calls.args.base import Argument
from hyperstone.plugins.hooks.base import HyperstoneCallback, ContextType
from hyperstone.emulator import HyperEmu

CB_EMU = 1
CB_CTX = 1

ExtendedCallback = Callable[[HyperEmu, ContextType], Any]


class CallingConvention:
    def __init__(self):
        self.respect_defaults = True

    @abstractmethod
    def __iter__(self) -> Iterator[Argument]:
        pass

    def __call__(self, function: Callable, *args, **kwargs) -> HyperstoneCallback:
        amount = self._calculate_needed(function, *args, compensate=CB_EMU)
        return self._generate_fn(function, amount, *args, **kwargs, pass_emu=True, pass_ctx=False)

    def ctx(self, function: Callable, *args, **kwargs) -> HyperstoneCallback:
        amount = self._calculate_needed(function, *args, compensate=(CB_EMU + CB_CTX))
        return self._generate_fn(function, amount, *args, **kwargs, pass_emu=True, pass_ctx=True)

    def _generate_fn(self, function: Callable, arg_amount: int, *args, pass_emu: bool, pass_ctx: bool, **kwargs):
        def call_wrapper(mu: HyperEmu, ctx: ContextType):
            amount = arg_amount
            params = []

            if pass_emu:
                params.append(mu)
            if pass_ctx:
                params.append(ctx)

            for arg in iter(self):
                if amount <= 0:
                    break

                params.append(arg.get(mu))
                amount -= 1

            return function(*params, *args, **kwargs)

        return call_wrapper

    def argcount(self, function: Callable) -> int:
        func_call = function
        if not inspect.isroutine(func_call):
            # Usually means __call__ override.
            # Since argument is Callable, it means we have __call__
            # noinspection PyUnresolvedReferences
            func_call = func_call.__call__

        func_code: types.CodeType = func_call.__code__

        positional_count = func_code.co_argcount + func_code.co_posonlyargcount

        if self.respect_defaults and func_call.__defaults__ is not None:
            # We respect defaults (by default). We can override them by changing __init__
            positional_count -= len(func_call.__defaults__)

        return positional_count

    def _calculate_needed(self, function: ExtendedCallback, *args, compensate: int) -> int:
        positional_count = self.argcount(function) - compensate

        userargs_compensate = len(args)
        arg_pull_amount = positional_count - userargs_compensate

        assert userargs_compensate <= positional_count
        return arg_pull_amount
