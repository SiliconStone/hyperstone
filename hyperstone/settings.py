from typing import Iterable, TYPE_CHECKING, Optional

from hyperstone.plugins.base import Plugin


if TYPE_CHECKING:
    # Import most plugins for better IDE autocompletion
    from hyperstone import plugins


class MetaSetting(type):
    """
    This metaclass implements iter() for classes, retrieving only the `Plugin`s inside it
    This allows using a class as Settings, which might be a better syntax than a List

    This also implements repr() for the class, supplying a better print output for a Settings class

    Notes:
        - All plugins that start and end with `_` (_SOME_PLUGIN_ = ...) will not be returned and as such will be ignored
            by the hyperstone engine, this allows for keeping plugins inside the class without having them being used
        - Any attribute that starts with `_` will not be printed by the repr(), this allows for skipping prints of
            trivial plugins and having better control over the output.
        - Any attribute that is `None` will be ignored by the repr()
    """
    def __iter__(cls):
        # This is done to allow pushing imported plugins while running
        items = list(vars(cls))
        for item in items:
            if item.startswith('_') and item.endswith('_'):
                continue

            obj = getattr(cls, item)
            if not isinstance(obj, Plugin):
                continue

            yield obj

    def __repr__(cls):
        out = f'{cls.__name__}:\n'

        for item in vars(cls):
            if item.startswith('_'):
                continue
            if item is None:
                continue

            is_hex = False
            value = getattr(cls, item)

            if isinstance(value, int):
                is_hex = True
            if isinstance(value, bool):
                is_hex = False

            out += f'\t{item}: '
            if is_hex:
                out += f'0x{value:08X}\n'
            else:
                out += f'{value}\n'

        return out


class Settings(metaclass=MetaSetting):
    """
    Legacy Settings class for supplying hyperstone plugins, might be useful for backwards compatible syntax
    or for more explicit plugin naming and control.
    You may use a normal List instead, but this syntax is more explicit and overall more organised.

    Notes:
        - This class also offers some "example" plugins that are set to `None` by default
        - Most of the magic here is just the `MetaSettings` metaclass, the rest is just for convenience

    Attributes:
        _STACK:
            Map the stack segment for the emulator
        SEGMENTS:
            Allows mapping empty segments into the memory. You should use `StreamMapper` for most cases.
        MEMORY:
            Allows mapping data into the memory, creating a segment in the process.
        PATCHES:
            Allows writing data into the memory without creating a segment, good for memory patches.
        ENFORCE_PERMS:
            Allows better (yet slower) permission enforcing, See `EnforceMemory` for more details.

        PE_LOADER:
            Allows loading a PE file (.exe/.dll) into memory. This loader was made specifically for hyperstone.
        CLE_LOADER:
            A generic loader based on `cle`. It has partial support in hyperstone.

        HOOKS:
            Allows setting hooks! The backbone of all cool hyperstone things.
        STUBS:
            Allows setting simple hooks that just return a specific value. These hooks must be set on the first opcode
            of the function.
        REGISTRY:
            Allows converting python objects to ints, which may be used to bridge between "emuland" objects and
            hyperstone-land objects.

        FUNCTIONS:
            Allows wrapping emulated functions as a python function, letting the user call them at will.
        PREPARE:
            Allows supplying a python function that runs before the emulator starts execution. Letting the user
            set registers / memory before execution.

        START:
            Allows setting an initial `pc` and running the emulator, not stopping until an exception is raised.
        ENTRYPOINT:
            Allows setting an entrypoint, the emulator will run until it reaches the last return statement in the given
            function.
        GDBSERVER:
            Allows exporting a GDB Server instead of actually running the emulator.
    """
    # Memory plugins
    _STACK: Optional['plugins.memory.InitializeSupportStack'] = None

    SEGMENTS: Optional['plugins.memory.Segment'] = None
    MEMORY: Optional['plugins.memory.StreamMapper'] = None
    PATCHES: Optional['plugins.memory.StreamWriter'] = None

    ENFORCE_PERMS: Optional['plugins.memory.EnforceMemory'] = None

    # Loaders
    PE_LOADER: Optional['plugins.loaders.PELoader'] = None
    CLE_LOADER: Optional['plugins.loaders.CLELoader'] = None

    # Hooks
    HOOKS: Optional['plugins.hooks.Hook'] = None
    STUBS: Optional['plugins.hooks.FunctionNullsub'] = None
    # Note, this class skips advanced plugins such as the fake object and fake dll plugins.
    REGISTRY: Optional['plugins.hooks.VirtualRegistry'] = None

    # Interfaces
    FUNCTIONS: Optional['plugins.interfaces.ExportFunction'] = None
    PREPARE: Optional['plugins.interfaces.PreparePlugin'] = None

    # Runners
    START: Optional['plugins.runners.Entrypoint'] = None
    ENTRYPOINT: Optional['plugins.runners.FunctionEntrypoint'] = None
    GDBSERVER: Optional['plugins.runners.GDBServer'] = None


SettingsType = Iterable[Plugin]
