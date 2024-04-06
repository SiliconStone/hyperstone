import abc
from abc import abstractmethod
from typing import Optional, Iterable, Type, TypeVar, List, Any

from hyperstone.emulator import HyperEmu
from hyperstone.exceptions import HSPluginNotFoundError
from hyperstone.util import log

IMPORTED_PLUGIN_NAME = 'HYPERSTONE_REQUIRE__{name}_'


class Plugin:
    _INTERACT_TYPE = TypeVar('_INTERACT_TYPE')
    _PLUGIN_TYPE = TypeVar('_PLUGIN_TYPE', bound='Plugin')

    @property
    def plugin_identity(self) -> List[Type]:
        return [type(self), Plugin]

    def __init__(self, *args: List[Any]):
        self._interact_queue = []
        self._interact_queue += args
        self.emu: Optional[HyperEmu] = None

    @property
    def ready(self) -> bool:
        return self.emu is not None

    def prepare(self, emu: HyperEmu):
        if self.ready:
            return

        self.emu = emu
        self._prepare()

        self._handle_all_interact(*self._interact_queue)
        self._interact_queue.clear()

    def interact(self, *objs: '_INTERACT_TYPE'):
        if self.ready:
            self._handle_all_interact(*objs)
        else:
            self._interact_queue += objs

    def _handle_all_interact(self, *objs: '_INTERACT_TYPE'):
        for obj in objs:
            self._handle(obj)

    def _prepare(self):
        """
        Users should override this in case the plugin needs to be prepared.
        :return: None
        """
        pass

    @abstractmethod
    def _handle(self, obj: '_INTERACT_TYPE'):
        pass

    @staticmethod
    def get_loaded(plugin: Type[_PLUGIN_TYPE], emu: HyperEmu) -> _PLUGIN_TYPE:
        for loaded in Plugin.get_all_loaded(plugin, emu):
            return loaded
        else:
            raise HSPluginNotFoundError(f'{plugin} is not loaded')

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
            if plugin in has_plugin.plugin_identity:
                yield has_plugin


class RunnerPlugin(Plugin):
    def run(self):
        if not self.ready:
            log.error('Attempted to call run too early!')
        else:
            self._run()

    @abstractmethod
    def _run(self):
        pass
