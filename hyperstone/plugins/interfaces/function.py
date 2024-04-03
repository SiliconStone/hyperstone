from dataclasses import dataclass
from typing import List, Optional, Dict

from hyperstone.plugins.base import Plugin
from hyperstone.plugins.runners import FunctionEntrypoint
from hyperstone.emulator import HyperEmu
from hyperstone.exceptions import HyperstonePluginError, HSPluginInteractNotReadyError
from hyperstone.util import log


@dataclass
class FunctionInfo:
    name: str
    address: int
    arguments: List[str]

class ExportFunction(Plugin):
    def __init__(self, *objs: FunctionInfo):
        super().__init__(*objs)
        self.functions: Dict[str, FunctionInfo] = {}
        self.runner: Optional[FunctionEntrypoint] = None

    def _handle_interact(self, *objs: FunctionInfo):
        for obj in objs:
            self.functions[obj.name] = obj

    def prepare(self, emu: HyperEmu):
        self.runner = Plugin.require(FunctionEntrypoint, emu)
        super().prepare(emu)

    def __getitem__(self, name):
        if name not in self.functions:
            raise HyperstonePluginError(f'Function "{name}" doesn\'t exist')

        return ExportedFunctionCaller(self, self.functions[name])


class ExportedFunctionCaller:
    def __init__(self, parent: ExportFunction, function: FunctionInfo):
        self._parent = parent
        self._function = function

    def __call__(self, *args):
        if not self._parent.ready:
            raise HSPluginInteractNotReadyError(f'Cannot run function "{self._function.name}" before preparing')

        emu = self._parent.emu
        runner = self._parent.runner

        if len(args) > len(self._function.arguments):
            log.error(f'Passing too many arguments, ignoring last {len(args) - len(self._function.arguments)} arguments')
            args = args[:len(self._function.arguments)]

        for i, arg in enumerate(args):
            emu.regs[self._function.arguments[i]] = arg

        runner.entrypoint = self._function.address
        runner.run()

        return emu.regs[emu.arch.retval_reg.name]
