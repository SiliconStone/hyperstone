from typing import Dict, List
from collections import defaultdict
from hyperstone.util.logger import log
from hyperstone.plugins.base import Plugin
from hyperstone.plugins.hooks import Hook, HookInfo

GLOBAL_FUNCTION_INDEX = 1


class Object:
    def __init__(self, name: str) -> None:
        self.name = name
        self.functions = defaultdict(lambda: 0)

    def add_dummy_function(self, name: str) -> None:
        """
        We don't want to program to exit for non implemented functions
        and we want to know which function did we try to jump to
        """
        global GLOBAL_FUNCTION_INDEX
        self.functions[name] = GLOBAL_FUNCTION_INDEX
        GLOBAL_FUNCTION_INDEX += 1


# Map Object's name to its handle
EXPORT_OBJECT_RESOLVER: Dict[str, int] = {}
# Map Object's address to the class which contains the functions it contains
EXPORT_FUNCTION_RESOLVER: Dict[int, Object] = {}


class FakeObject(Plugin):
    def __init__(self, *args: str):
        """
        Hooks functions it receives in args, their format should be ObjectName!FunctionName
        """
        self.function_list: List[str] = [*args]
        super().__init__()

    def _prepare(self) -> None:
        """
        Create hooks for all the exported object's functions
        """
        self._hook_plugin = Plugin.require(Hook, self.emu)
        for export_name in self.function_list:
            object_name, function_name = export_name.split("!")
            export_address = self._resolve_export(object_name, function_name)
            log.debug(
                f'{object_name}!{function_name}@{"None" if not export_address else hex(export_address)}'
            )
            if export_address is not None:
                self._hook_plugin.interact(
                    HookInfo(
                        f'{type(self).__name__}.{object_name}!{function_name}',
                        export_address,
                        None,
                        getattr(self, function_name),
                    )
                )

    def _resolve_export_fallback(
        self, object_name: str, function_name: str
    ) -> int | None:
        """
        Implement this to help resolve exported functions using the correct loader
        """
        pass

    def _resolve_export(self, object_name: str, function_name: str) -> int | None:
        """
        Returns the address on which a hook for the function should be placed
        """
        object_address = self._get_or_add_object(object_name)
        if not object_address in EXPORT_FUNCTION_RESOLVER:
            EXPORT_FUNCTION_RESOLVER[object_address] = Object(object_name)

        current_object = EXPORT_FUNCTION_RESOLVER[object_address]
        if not function_name in current_object.functions:
            fallback_result = self._resolve_export_fallback(object_name, function_name)
            if fallback_result:
                current_object.functions[function_name] = fallback_result
            else:
                current_object.add_dummy_function(function_name)

        return current_object.functions[function_name]

    def _create_or_resolve_object_handle(self, name: str) -> int:
        """
        Implement this to return an object which a library resolves to for the ran program
        """
        pass

    def _get_or_add_object(self, name: str) -> int:
        """
        Utility function to add fake libraries or return exiting fake libraries' handles
        """
        if name not in EXPORT_OBJECT_RESOLVER:
            EXPORT_OBJECT_RESOLVER[name] = self._create_or_resolve_object_handle(name)
        return EXPORT_OBJECT_RESOLVER[name]

    def _get_function_address(self, object_handle: int, function_name: str) -> int:
        """
        Utility function to get fake function addresses by objects handle and the function name
        """
        object_base_to_names = {v: k for k, v in EXPORT_OBJECT_RESOLVER.items()}
        if object_handle not in EXPORT_FUNCTION_RESOLVER:
            log.error(f'Object {object_base_to_names[object_handle]} not implemented')
        elif function_name not in EXPORT_FUNCTION_RESOLVER[object_handle].functions:
            log.error(f'Function {function_name} not implemented')
        else:
            return EXPORT_FUNCTION_RESOLVER[object_handle].functions[function_name]

        return self._fallback_get_function_address(
            object_base_to_names[object_handle], function_name
        )

    def _fallback_get_function_address(
        self, object_name: str, function_name: str
    ) -> int:
        """
        Let the inheriting classes resolve a function's address manually
        """
        pass
