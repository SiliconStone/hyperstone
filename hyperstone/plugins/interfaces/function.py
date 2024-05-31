from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any, Type

from hyperstone.plugins.base import Plugin, RunnerPlugin
from hyperstone.plugins.runners import FunctionEntrypoint
from hyperstone.exceptions import HyperstonePluginError, HSPluginInteractNotReadyError
from hyperstone.util.logger import log


@dataclass(frozen=True)
class ExportFunctionInfo:
    name: str
    address: int
    arguments: Tuple[str, ...]


class ExportFunction(Plugin):
    def __init__(self, *objs: ExportFunctionInfo):
        super().__init__(*objs)
        self.functions: Dict[str, ExportFunctionInfo] = {}
        self._runner = FunctionEntrypoint
        self._args = {}

    def _prepare(self):
        pass

    def _handle(self, obj: ExportFunctionInfo):
        self.functions[obj.name] = obj

    def __getitem__(self, name):
        if name not in self.functions:
            raise HyperstonePluginError(f'Function "{name}" doesn\'t exist')

        return ExportedCaller(self, self.functions[name], self._runner, self._args)


class ExportedCaller:
    def __init__(self, parent: ExportFunction, function: ExportFunctionInfo,
                 runner: Type[RunnerPlugin], args: Optional[Dict[str, Any]] = None):
        self._parent = parent
        self._function = function
        self._runner = runner
        if args is None:
            args = {}
        self._args = args

    def __call__(self, *args):
        if not self._parent.ready:
            raise HSPluginInteractNotReadyError(f'Cannot run "{self._function.name}" before preparing')

        emu = self._parent.emu
        runner = Plugin.require(self._runner, emu)

        if len(args) > len(self._function.arguments):
            log.error(f'Passing too many arguments, ignoring last '
                      f'{len(args) - len(self._function.arguments)} arguments')
            args = args[:len(self._function.arguments)]

        for i, arg in enumerate(args):
            emu.regs[self._function.arguments[i]] = arg

        runner.entrypoint = self._function.address

        for arg, val in self._args.items():
            setattr(runner, arg, val)

        runner.run()

        return emu.regs[emu.arch.retval_reg.name]
