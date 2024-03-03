from .emulator import HyperEmu
from .settings import SettingsType
from .plugins import RunnerPlugin
from .util import log

import megastone as ms


def start(arch: ms.Architecture, settings: SettingsType) -> HyperEmu:
    emu = HyperEmu(arch, settings)

    runner = None
    for plugin in settings:
        plugin.prepare(emu)
        if isinstance(plugin, RunnerPlugin):
            if runner:
                raise ValueError(f'Cannot have two runner plugins ({runner} and {plugin})')
            runner = plugin

    if not runner:
        log.error(f'No runner plugin supplied!')
    else:
        runner.run()

    return emu
