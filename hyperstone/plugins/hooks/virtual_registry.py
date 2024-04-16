from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, Optional, List

from hyperstone.plugins.base import Plugin
from hyperstone.exceptions import HSPluginInteractionError
from hyperstone.util.logger import log


class RegistryAction(Enum):
    CREATE = auto()  # Create a new object and get fd
    DELETE = auto()  # Close fd


@dataclass
class VirtualRegistryInfo:
    action: RegistryAction
    value: Any
    hints: Optional[List[str]] = None


class VirtualRegistry(Plugin):
    _INTERACT_TYPE = VirtualRegistryInfo

    def __init__(self, *args: VirtualRegistryInfo):
        super().__init__(*args)
        self._registry: Dict[int, Any] = {}
        self._hints: Dict[int, List[str]] = {}
        self._fd = 0

    @property
    def last_fd(self) -> int:
        return self._fd - 1

    def _make_fd(self):
        fd = self._fd
        self._fd += 1
        return fd

    def _handle(self, obj: VirtualRegistryInfo):
        log.info(f'VirtualRegistry - [{obj.value}].{obj.action}')
        if obj.action == RegistryAction.CREATE:
            new_fd = self._make_fd()
            self._registry[new_fd] = obj.value

            if obj.hints is not None:
                self._hints[new_fd] = obj.hints
        elif obj.action == RegistryAction.DELETE:
            if obj.value not in self._registry:
                raise HSPluginInteractionError(f'fd doesn\'t exist - {obj.value}')

            del self._registry[obj.value]
            del self._hints[obj.value]
        else:
            raise HSPluginInteractionError(f'Unknown action "{obj.action}"')

    def search(self, *hints: str) -> int:
        for fd, item_hints in self._hints.items():
            for hint in hints:
                if hint in item_hints:
                    return fd

        raise ValueError(f'Hints found nothing (hints: {hints})')

    def __getitem__(self, fd: int) -> Any:
        if fd not in self._registry:
            raise ValueError(f'Invalid fd {fd}')

        return self._registry[fd]
