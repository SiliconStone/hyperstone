from typing import Optional, TYPE_CHECKING

from hyperstone.emulator import HyperEmu

if TYPE_CHECKING:
    from hyperstone.plugins.hooks.base import ActiveHook


class Context:
    def __init__(self):
        self.emu: Optional[HyperEmu] = None
        self.hook: Optional['ActiveHook'] = None


class DictContext(Context, dict):
    def __new__(cls, *args, **kwargs):
        return dict.__new__(cls, *args, **kwargs)

    def __init__(self, initial_dict: dict = None, **initial_values):
        super().__init__()
        if initial_dict is not None:
            self.update(initial_dict)
        self.update(initial_values)
