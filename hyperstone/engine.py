from typing import Tuple, Optional
import megastone as ms

from hyperstone.emulator import HyperEmu
from hyperstone.plugins import RunnerPlugin
from hyperstone.settings import SettingsType
from hyperstone.util import log


def prepare(arch: ms.Architecture, settings: SettingsType) -> Tuple[HyperEmu, Optional[RunnerPlugin]]:
    emu = HyperEmu(arch, settings)

    runner = None
    for plugin in settings:
        plugin.prepare(emu)
        if isinstance(plugin, RunnerPlugin):
            if runner:
                raise ValueError(f'Cannot have two runner plugins ({runner} and {plugin})')
            runner = plugin

    if not runner:
        log.warning(f'No runner plugin supplied!')

    return emu, runner


def start(arch: ms.Architecture, settings: SettingsType) -> HyperEmu:
    emu, runner = prepare(arch, settings)

    if runner:
        runner.run()

    return emu
