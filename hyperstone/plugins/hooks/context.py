from typing import Optional, TYPE_CHECKING


if TYPE_CHECKING:
    from hyperstone.emulator import HyperEmu
    from hyperstone.plugins.hooks.base import ActiveHook


class Context:
    """
    A context object that would be passed to a Hook callback.
    This object should be used to store data between calls to the hook's callback

    Attributes:
        emu: The emulator instance.
        hook: The active hook instance, including both the `HookInfo` and the actual megastone hook project.
    """
    def __init__(self):
        self.emu: Optional['HyperEmu'] = None
        self.hook: Optional['ActiveHook'] = None


class DictContext(Context, dict):
    """
    A context object that can also be used as a `dict`
    When you don't specify a ctx for a `HookInfo` object, this object is used
    This allows users to use the context object freely, though this practice is frowned upon.

    Notes:
        Users should inherit from `Context` instead of using this object, however this object is supplied as a quick
        hack to some hyperstone objects.
    """
    def __new__(cls, *args, **kwargs):
        return dict.__new__(cls, *args, **kwargs)

    def __init__(self, initial_dict: dict = None, **initial_values):
        super().__init__()
        if initial_dict is not None:
            self.update(initial_dict)
        self.update(initial_values)
