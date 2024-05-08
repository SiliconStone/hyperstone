import abc
from abc import abstractmethod
from itertools import chain
from typing import Optional, Iterable, Type, TypeVar, List, Any

from hyperstone.emulator import HyperEmu
from hyperstone.exceptions import HSPluginNotFoundError
from hyperstone.util import log, LazyResolver

IMPORTED_PLUGIN_NAME = 'HYPERSTONE_REQUIRE__{name}_'


class Plugin:
    """
    This class represents a plugin.

    Attributes:
        _INTERACT_TYPE: may be used to inform an IDE / a developer the designated interact type
    """
    _INTERACT_TYPE = TypeVar('_INTERACT_TYPE')
    _PLUGIN_TYPE = TypeVar('_PLUGIN_TYPE', bound='Plugin')

    @property
    def plugin_identity(self) -> List[Type]:
        """
        The identity of the plugin.
        This is used when trying to require() / get_loaded() a plugin

        Override this in order to declare a plugin as another, and allowing Hyperstone to use said plugin instead
        of creating a new instance of a "primitive" one.

        Returns:
            A list of classes / Interfaces that this plugin implements.
        """
        return [type(self), Plugin]

    def __init__(self, *args: '_INTERACT_TYPE'):
        """
        Supply actions to this plugin.
        This should be used by the user in their Settings object
        You may supply no arguments to this plugin, hyperstone assumes this behaviour for require.

        Args:
            *args:
                Arguments passed to this plugin, each one represents an action
                Arguments passed to Plugin.__init__() should have the same format as ones passed to interact()
                **Note that the plugin should support calling __init__() with no arguments**.
        """
        self._interact_queue = []
        self._interacted = []
        self.emu: Optional[HyperEmu] = None

        self.interact(*args)

    def __call__(self, *args: '_INTERACT_TYPE'):
        """
        Alternative way to interact with this plugin.
        """
        self.interact(*args)
        return self

    def __getitem__(self, item):
        """
        A way to obtain data from a plugin.

        Raises:
            NotImplementedError: In case that the plugin doesn't implement __getitem_
        """
        raise NotImplementedError('No Implementation for getting items from this plugin')

    def __matmul__(self, item) -> LazyResolver:
        """
        Alias for __getitem__ but using a LazyResolver.
        This allows the user to ask for data that isn't there yet

        For example, we can use a LazyResolver to get a segment's base address before it was even mapped.
        The syntax is the same as using __getitem__.

        Args:
            item: Same as __getitem__

        Returns:
            A LazyResolver for plugin[item]
        """
        return LazyResolver(self)[item]

    @property
    def ready(self) -> bool:
        """
        Whether this plugin was prepared.
        In reality, a "ready" plugin is a plugin that has an instance of our emulator.

        Returns:
            True if the plugin is ready, False otherwise.
        """
        return self.emu is not None

    def prepare(self, emu: HyperEmu):
        """
        Prepare this plugin.
        This function will do nothing if we were prepared.
        This function will also trigger a flush of all interact()s / values that were supplied in __init__()
        Code may call this function for another plugin if the logic requires the plugin to run an action instantly.

        Example, map a segment and write data. In that case we'd have to map a segment instantly (and write later)
        As such, we'd have to prepare() the mapper plugin

        Args:
            emu: The instance of our emulator.
        """
        if self.ready:
            return

        self.emu = emu
        self._prepare()

        self._handle_all_interact(*self._interact_queue)
        self._interact_queue.clear()

    def interact(self, *objs: '_INTERACT_TYPE'):
        """
        Interact with this plugin - requesting it to run its default behaviour.
        Note that if the plugin wasn't prepared it may run this action at some point before running the emulator.

        Args:
            objs: Objects that contain the action to be performed (usually a dataclass for this specific plugin).
        """
        if self.ready:
            self._handle_all_interact(*objs)
        else:
            self._interact_queue += objs

    def _handle_all_interact(self, *objs: '_INTERACT_TYPE'):
        for obj in objs:
            self._handle(obj)
            self._interacted.append(obj)

    def _prepare(self):
        """
        Users should override this in case the plugin needs to be prepared in a specific way.
        """
        pass

    @property
    def get_interacted(self) -> List['_INTERACT_TYPE']:
        """
        Retrieve a List of all interacted object, whether they were handled already or not.

        Returns:
            A List of all interact() objects
        """
        return self._interact_queue + self._interacted

    @abstractmethod
    def _handle(self, obj: '_INTERACT_TYPE'):
        """
        The function that runs an action for one interact object.

        Args:
            obj: The object to handle.
        """
        pass

    @staticmethod
    def get_loaded(plugin: Type[_PLUGIN_TYPE], emu: HyperEmu) -> _PLUGIN_TYPE:
        """
        Get an instance of a specified plugin class from our Settings object.

        Args:
            plugin: Class of the plugin to find.
            emu: Our emulator.

        Returns:
            An instance of a specified plugin class.

        Raises:
            HSPluginNotFoundError: If specified plugin class is not found.
        """
        for loaded in Plugin.get_all_loaded(plugin, emu):
            return loaded
        else:
            raise HSPluginNotFoundError(f'{plugin} is not loaded')

    @staticmethod
    def require(plugin: Type[_PLUGIN_TYPE], emu: HyperEmu) -> _PLUGIN_TYPE:
        """
        Get an instance of a specified plugin class or load it if needed.
        This function will try to find an existing instance of specified plugin.
        If it doesn't exist, it will be created.

        Args:
            plugin: The plugin to find
            emu: Our emulator.

        Returns:
            An instance of our requested plugin.
        """
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
        """
        Get all instances of specified plugin class.

        Args:
            plugin: The plugin class(es) to find.
            emu: Our emulator

        Returns:
            An iterable of all instances of specified plugin.
        """
        for has_plugin in emu.settings:
            if plugin in has_plugin.plugin_identity:
                yield has_plugin


class RunnerPlugin(Plugin):
    """
    A plugin that is able to start the Emulator.
    """
    def run(self):
        """
        Start the emulation.
        Unlike _run(), this function also checks that the emulator has passed the prepare() stage.
        """
        if not self.ready:
            log.error('Attempted to call run too early!')
        else:
            self._run()

    @abstractmethod
    def _run(self):
        """
        This function is called to start the emulation.
        """
        pass
