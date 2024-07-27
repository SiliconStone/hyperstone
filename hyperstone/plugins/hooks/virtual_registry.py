from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, Optional, List, Iterator

from hyperstone.plugins.base import Plugin
from hyperstone.exceptions import HSPluginInteractionError
from hyperstone.util.logger import log


class RegistryAction(Enum):
    """
    Represents an action to be performed on a virtual registry.

    Attributes:
        CREATE: Create a new virtual registry object, putting it in the registry
        DELETE: Delete a virtual registry object by fd
    """
    CREATE = auto()  # Create a new object and get fd
    DELETE = auto()  # Close fd


@dataclass
class VirtualRegistryInfo:
    """
    Represents a virtual registry action, mostly affecting the items present in the registry

    Attributes:
        action:
            The action to take on the virtual registry.
        value:
            The item to affect.
            If the action is CREATE, the item will be added to the registry
            If the action is DELETE, the value will be treated as a fd (file descriptor / ID)
        hints:
            Optional hints to give for the object when creating it, used as keywords for the search methods
    """
    action: RegistryAction
    value: Any
    hints: Optional[List[str]] = None


class VirtualRegistry(Plugin):
    """
    This plugin provides an interface to store python objects and identify them by IDs
    It is most useful as a way to let a program manage memory / context-like objects in its own way.
    It lets you add and remove python objects, which can later be retrieved by an `int` called `fd`.
    A user may create an object (be it file, string, dict, etc.) and retrieve its `fd`, which can be given back
    to the emulated program (and be resolved later on to its corresponding object).

    Notes:
        This plugin doesn't actually open files, the term `fd` is used as an internal ID for each object
    """
    _INTERACT_TYPE = VirtualRegistryInfo

    def __init__(self, *args: VirtualRegistryInfo):
        super().__init__(*args)
        self._registry: Dict[int, Any] = {}
        self._hints: Dict[int, List[str]] = {}
        self._fd = 0

    @property
    def last_fd(self) -> int:
        """
        Retrieve the last created `fd`, easiest way to get an `fd` after creating an object.

        Returns:
            The last created `fd`.
        """
        return self._fd - 1

    def _make_fd(self):
        fd = self._fd
        self._fd += 1
        return fd

    def _handle(self, obj: VirtualRegistryInfo):
        """
        Add or remove a single item.

        Args:
            obj: The item to be added / removed, as specified via `VirtualRegistryInfo`
        """
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

    def search_all(self, *hints: str, require_all: bool = False) -> Iterator[int]:
        """
        Find all items that match the given criteria and hints.

        Args:
            *hints: Hints to look for
            require_all: Should the resulted item match all the hints or should it match at least one?

        Returns:
            An iterator over all `fd`s that match the given criteria.
        """
        for fd, item_hints in self._hints.items():
            for hint in hints:
                if hint not in item_hints:
                    break
                if not require_all:
                    yield fd
            else:
                yield fd

    def search(self, *hints: str, require_all: bool = False) -> int:
        """
        Search for the first item that match the given criteria and hints.

        Args:
            *hints: Hints to look for
            require_all: Should the resulted item match all the hints or should it match at least one?

        Returns:
            The matched item's `fd` if found

        Raises:
            ValueError: If no item matches the given criteria.
        """
        for result in self.search_all(*hints, require_all=require_all):
            return result

        raise ValueError(f'Hints found nothing (hints: {hints})')

    def __getitem__(self, fd: int) -> Any:
        """
        Resolve an object by fd.

        Args:
            fd: The `fd` to resolve.

        Returns:
            The corresponding object.

        Raises:
            ValueError: If the registry doesn't contain the given `fd` (bad `fd` / already closed)
        """
        if fd not in self._registry:
            raise ValueError(f'Invalid fd {fd}')

        return self._registry[fd]
