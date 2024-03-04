from abc import abstractmethod, ABC

from ..emulator import HyperEmu
from ..util import log

from typing import Optional, Iterable, Type, TypeVar, TYPE_CHECKING


IMPORTED_PLUGIN_NAME = 'HYPERSTONE_REQUIRE__{name}_'


class Plugin:
    _INTERACT_TYPE = TypeVar('_INTERACT_TYPE')
    _PLUGIN_TYPE = TypeVar('_PLUGIN_TYPE', bound='Plugin')

    def __init__(self):
        self.interact_queue = []
        self.emu: Optional[HyperEmu] = None

    @property
    def ready(self) -> bool:
        return self.emu is not None

    def prepare(self, emu: HyperEmu):
        self.emu = emu
        self._handle_interact(*self.interact_queue)
        self.interact_queue.clear()

    def interact(self, *objs: '_INTERACT_TYPE'):
        if self.ready:
            self._handle_interact(*objs)
        else:
            self.interact_queue += objs

    @abstractmethod
    def _handle_interact(self, *objs: '_INTERACT_TYPE'):
        pass

    @staticmethod
    def require(plugin: Type[_PLUGIN_TYPE], emu: HyperEmu) -> _PLUGIN_TYPE:
        for loaded in Plugin.get_all_loaded(plugin, emu):
            return loaded
        new_plug: Plugin = plugin()

        if isinstance(emu.settings, list):
            emu.settings.append(new_plug)
        else:
            setattr(emu.settings, IMPORTED_PLUGIN_NAME.format(name=plugin.__name__), new_plug)

        new_plug.prepare(emu)
        return new_plug

    @staticmethod
    def get_all_loaded(plugin: Type[_PLUGIN_TYPE], emu: HyperEmu) -> Iterable[_PLUGIN_TYPE]:
        for has_plugin in emu.settings:
            if isinstance(has_plugin, plugin):
                yield has_plugin


class RunnerPlugin(Plugin, ABC):
    def run(self):
        if not self.ready:
            log.error('Attempted to call run too early!')
        else:
            self._run()

    @abstractmethod
    def _run(self):
        pass
