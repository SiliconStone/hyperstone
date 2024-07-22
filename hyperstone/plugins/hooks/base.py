from dataclasses import dataclass, field
from functools import partial
from typing import Optional, Callable, Any, Tuple, Union, List, TypeVar

import megastone as ms

from hyperstone.plugins.base import Plugin
from hyperstone.emulator import HyperEmu
from hyperstone.exceptions import HSHookAlreadyRemovedError
from hyperstone.util.logger import log
from hyperstone.plugins.hooks.context import Context, DictContext


HookFunc = Callable[[HyperEmu], Any]
HyperstoneCallback = Callable[[Context], Any]
KC = TypeVar('KC', bound=Context)  # Support for old python


@dataclass
class HookInfo:
    """
    The base hook info class.
    Defines a hook.

    Attributes:
        name:
            The name of the hook.
        address:
            The address to set a hook on, supports LazyResolver
            If `address` is `None`, `size` is ignored and the hook will affect all addresses.
        return_address:
            An address to set the program counter (PC) after running the hook.
            Optional, supports LazyResolver
        callback:
            A callback to run when the hook is triggered
            HyperstoneCallback - Accepts a Context object.
            Optional
        size:
            the amount of bytes that the hook is bound to. Ignored if `address` is `None`.
        ctx:
            A Context object that will be passed to the callback.
            By default, The context object is a DictContext instance, acting as a `dict`
            A user may inherit the Context base class to implement more advanced Context "requirements" for hooks.
    """
    name: str
    address: Optional[Union[int, Callable[[], int]]]
    return_address: Optional[Union[int, Callable[[], int]]] = None
    callback: Optional[HyperstoneCallback] = None
    size: int = 1
    ctx: KC = field(default_factory=DictContext)
    double_call: bool = False

    _address: Union[int, Callable[[], int]] = field(init=False, repr=False)

    @property
    def address(self):
        return int(self._address) if self._address is not None else None

    @address.setter
    def address(self, value):
        self._address = value


@dataclass
class ActiveHook:
    """
    An object representing an active hook.
    Supplies the constructing `HookInfo`, as well as the `megastone` Hook object for internal access and management.
    Every instance of this object should be unique, as every instance of an `ms.Hook` object should be unique.
    You may use the same `HookInfo` multiple times in some cases (although it is not recommended, as `HookInfo` is not
    frozen).

    Attributes:
        info:
            The `HookInfo` object that was used to create this hook.
        obj:
            The `ms.Hook` object that was returned from the megastone engine.
            If `None`, then the hook was removed and does not represent any hook that is active
    """
    info: HookInfo
    obj: Optional[ms.Hook]

    @property
    def active(self) -> bool:
        return self.obj is not None


class Hook(Plugin):
    """
    Supplies a Hook management engine

    Attributes:
        SILENT:
            If a hook name starts with this constant, hyperstone will attempt to lower verbosity for this hook
            This includes (for example) the log function for when this hook is being triggered to be TRACE severity.
    """
    SILENT = '!'

    def __init__(self, *hooks: HookInfo):
        super().__init__()
        self._interact_queue += hooks
        self._hooks: List[ActiveHook] = []

    def __getitem__(self, item: str) -> ActiveHook:
        """
        Gets an active hook by name

        Args:
            item: The hook's name. Note that this function doesn't strip the `Hook.SILENT` prefix.

        Returns:
            The active hook with specified `name` if found.

        Raises:
            KeyError: If the hook is not active / wasn't registered
        """
        for hook in self._hooks:
            if hook.info.name == item:
                return hook

        raise KeyError(f'{item} not found.')

    def get(self, hook_info: HookInfo) -> ActiveHook:
        """
        Get a hook by `HookInfo` object.

        Args:
            hook_info: The `HookInfo` to look for.

        Returns:
            The active hook if found.

        Raises:
            KeyError: If the hook is not active / wasn't registered
        """
        for hook in self._hooks:
            if hook.info == hook_info:
                return hook

        raise KeyError(f'{hook_info} not found.')

    @property
    def hooks(self) -> Tuple[ActiveHook, ...]:
        """
        Get a Tuple of all active hooks.

        Returns:
            The tuple of active hooks.
        """
        return tuple(self._hooks)

    def _handle(self, hook: HookInfo):
        """
        Register a single CODE hook

        Args:
            hook: The hook to register
        """
        func = partial(Hook._hook, hook.ctx)
        hook.ctx.hook = self.add_hook(hook, func, ms.HookType.CODE)

    def add_hook(self, hook: HookInfo, func: Union[HookFunc, ms.HookFunc],
                 access_type: ms.HookType) -> ActiveHook:
        """
        An extended API for the hook plugin to register a hook.
        While this is a basic `megastone` hook wrapper, it's a good practice to use this function for several reasons:
        Using this method allows to keep track of active hooks, as well as get and remove by name / HookInfo
        It also allows an extending Hook plugin to override this function to allow more advanced hook tracking.

        Args:
            hook:
                The HookInfo to register
            func:
                A callback function, by default, this function gets a megastone `Debugger` object,
                but when called with a hyperstone emulator, this function will get a `HyperEmu` object.
            access_type:
                Access type that'd trigger this hook.
        Returns:

        """
        ms_hook = self.emu.add_hook(func, access_type, hook.address, hook.size)
        active = ActiveHook(hook, ms_hook)
        self._hooks.append(active)
        log.info(f'Added hook {hook.name}')
        return active

    def remove_hook(self, hook: ActiveHook):
        """
        An extended API for the hook plugin to remove a hook.

        Args:
            hook: The active hook to remove.

        Notes:
            This function will set `hook.obj` to `None` on success.
            This invalidates the `ActiveHook` object and it shouldn't be used afterward for any interaction with
            the `Hook` plugin.
        """
        if not hook.obj:
            raise HSHookAlreadyRemovedError(f'Hook {hook.info.name} already removed')

        self._hooks.remove(hook)
        self.emu.remove_hook(hook.obj)
        hook.obj = None

    @staticmethod
    def _hook(hook_ctx: Context, emu: HyperEmu):
        """
        The internal hook callback for when interacting with the plugin
        This function implements the `HookInfo.return_address` feature, as well as the `Context` mechanisms
        as well as debug printing on call.

        Args:
            hook_ctx: The context of this hook, should be supplied via `functools.partial()`
            emu: The emulator object, usually supplied from the internal hook engine
        """
        hook_info = hook_ctx.hook.info
        hook_ctx.emu = emu

        if hook_info.return_address is None:
            was_called = hook_info.double_call
            hook_info.double_call = False
            if was_called:
                return
        else:
            hook_info.return_address = int(hook_info.return_address)

        log_fn = log.trace if hook_info.name.startswith(Hook.SILENT) else log.info

        log_fn(f'Hook - {hook_info.name} [PC = 0x{emu.pc:08X}, RET = 0x{emu.retaddr:08X}]')
        old_pc = emu.pc
        func = hook_info.callback
        if func:
            try:
                func(hook_ctx)
            except Exception as e:
                log.error(f'Error calling {func}: {e}')

        if hook_info.return_address is not None:
            emu.pc = hook_info.return_address
        elif old_pc == emu.pc:
            hook_info.double_call = not hook_info.double_call
