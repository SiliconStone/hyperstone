from abc import abstractmethod
from typing import Callable, Any, Iterator
import inspect
import types

from hyperstone.calls.args.base import Argument
from hyperstone.plugins.hooks.base import HyperstoneCallback
from hyperstone.util.context import Context
from hyperstone.util.logger import log


CB_CTX = 1

ExtendedCallback = Callable[[Context], Any]


class CallingConvention:
    def __init__(self):
        self.respect_defaults = True

    @abstractmethod
    def __iter__(self) -> Iterator[Argument]:
        pass

    def __call__(self, function: Callable, *args, **kwargs) -> HyperstoneCallback:
        amount = self._calculate_needed(function, *args, compensate=CB_CTX)
        return self._generate_fn(function, amount, *args, **kwargs)

    def _generate_fn(self, function: Callable, arg_amount: int, *args, **kwargs):
        def call_wrapper(ctx: Context):
            amount = arg_amount
            params = [ctx]

            for arg in iter(self):
                if amount <= 0:
                    break

                params.append(arg.get(ctx.emu))
                amount -= 1
            log.trace(f'calling {function}')
            retval = function(*params, *args, **kwargs)
            log.trace(f'returned {retval}')
            return retval

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
