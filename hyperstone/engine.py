from typing import Tuple, Optional
import megastone as ms

from hyperstone.emulator import HyperEmu
from hyperstone.plugins.base import RunnerPlugin
from hyperstone.settings import SettingsType
from hyperstone.util.logger import log


def prepare(arch: ms.Architecture, settings: SettingsType) -> Tuple[HyperEmu, Optional[RunnerPlugin]]:
    """
    Make and prepare a hyperstone emulator without running it.
    This is useful if you have interface Plugins and you want to use the emulator in a more flexible way.

    Args:
        arch: The architecture of the Hyperstone emulator.
        settings: A settings object containing the plugins needed for the current emulation run

    Returns:
        An instance of the emulator before a run, but after all the plugins were loaded and prepared.
        An instance of a runner plugin that should've been used to run the emulator, if exists.
    """
    emu = HyperEmu(arch, settings)

    runner = None
    for plugin in settings:
        log.debug(f'Preparing plugin {plugin}...')
        plugin.prepare(emu)
        if isinstance(plugin, RunnerPlugin):
            if runner:
                log.error(f'Found two runner plugins ({runner} and {plugin}), Using [{plugin}]')
            runner = plugin

    return emu, runner


def start(arch: ms.Architecture, settings: SettingsType) -> HyperEmu:
    """
    Prepare and start the Hyperstone emulator.

    Args:
        arch: The architecture of the Hyperstone emulator.
        settings: A settings object containing the plugins needed for the current emulation run

    Returns:
        The instance of the emulator after a run.
    """
    emu, runner = prepare(arch, settings)

    if runner:
        log.debug(f'Executing runner {runner}')
        runner.run()
    else:
        log.error(f'No runner plugin supplied!')

    return emu
