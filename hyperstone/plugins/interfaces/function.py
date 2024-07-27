from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any, Type

from hyperstone.plugins.base import Plugin, RunnerPlugin
from hyperstone.plugins.runners import FunctionEntrypoint
from hyperstone.calls.base import CallingConvention
from hyperstone.exceptions import HyperstonePluginError, HSPluginInteractNotReadyError
from hyperstone.util.logger import log


@dataclass(frozen=True)
class ExportFunctionInfo:
    """
    Defines a function to be exported

    Attributes:
        name: The name of the function to be exported.
        address: The address of the function, on execute the emulator will jump to that address.
        convention: The calling convention of the function.
    """
    name: str
    address: int
    convention: CallingConvention


class ExportFunction(Plugin):
    """
    This plugin allows to "wrap" functions inside the emulated program as python-like functions.
    This allows the user to call a specific function many times from a python script with different arguments.
    This might be useful in cases that a user wants to run a specific function from a program over a chunk of data
    instead of emulating the entire program.
    """
    def __init__(self, *objs: ExportFunctionInfo):
        super().__init__(*objs)
        self.functions: Dict[str, ExportFunctionInfo] = {}
        self._runner = FunctionEntrypoint
        self._args = {}

    def _prepare(self):
        pass

    def _handle(self, obj: ExportFunctionInfo):
        self.functions[obj.name] = obj

    def __getitem__(self, name: str) -> 'ExportedCaller':
        """
        Get a function by name, see `ExportFunctionInfo`

        Args:
            name: The name of the function to get.

        Returns:
            An `ExportedCaller` instance that provides a `__call__` method for the given function.
            You may call a function by:
            plugin['FunctionName'](arg1, arg2, arg3, ...)

        Raises:
            HyperstonePluginError: If the function is not found.
        """
        if name not in self.functions:
            raise HyperstonePluginError(f'Function "{name}" doesn\'t exist')

        return ExportedCaller(self, self.functions[name], self._runner, self._args)


class ExportedCaller:
    """
    This object acts as a fake runner plugin which prepares the emulator for a single function run when `__call__`'d
    """
    def __init__(self, parent: ExportFunction, function: ExportFunctionInfo,
                 runner: Type[RunnerPlugin], runner_args: Optional[Dict[str, Any]] = None):
        self._parent = parent
        self._function = function
        self._runner = runner
        if runner_args is None:
            runner_args = {}
        self._args = runner_args

    def __call__(self, *args):
        if not self._parent.ready:
            raise HSPluginInteractNotReadyError(f'Cannot run "{self._function.name}" before preparing')

        emu = self._parent.emu
        runner = Plugin.require(self._runner, emu)

        for i, param in enumerate(self._function.convention):
            if len(args) == i:
                break
            param.set(emu, args[i])

        runner.entrypoint = self._function.address

        for arg, val in self._args.items():
            setattr(runner, arg, val)

        runner.run()

        return emu.regs[emu.arch.retval_reg.name]
