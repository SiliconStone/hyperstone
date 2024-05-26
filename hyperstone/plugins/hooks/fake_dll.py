from typing import Any, Dict
from hyperstone.util.logger import log
from hyperstone.emulator import HyperEmu
from hyperstone.plugins.base import Plugin
from hyperstone.plugins.hooks import FakeObject
from hyperstone.plugins.loaders import PELoader, PELoaderInfo
from hyperstone.plugins.loaders.pe import calculate_aslr, file_to_name, FileNameType


class FakeDll(FakeObject):

    def __init__(self, *args: str):
        super().__init__(
            "KERNEL32.DLL!LoadLibraryA",
            "KERNEL32.DLL!LoadLibraryW",
            "KERNEL32.DLL!GetProcAddress",
            *args,
        )

    def _prepare(self):
        self._pe = Plugin.require(PELoader, self.emu)
        self._pe.prepare(self.emu)
        super()._prepare()

    def _resolve_export_fallback(
        self, object_name: str, function_name: str
    ) -> int | None:
        if (
            object_name in self._pe._fake_exports
            and function_name in self._pe._fake_exports[object_name].functions
        ):
            return self._pe._fake_exports[object_name].functions[function_name]

        if object_name in self._pe:
            function_address = self._pe[object_name].function(
                function_name
            )
            if function_address:
                return function_address

    def _create_or_resolve_object_handle(self, name: str) -> int:
        if name not in self._pe:
            self._pe.interact(PELoaderInfo(name))
        if name in self._pe:
            return self._pe[name].base
        elif name.lower() in self._pe._fake_exports:
            return self._pe._fake_exports[name.lower()].base
        else:
            return calculate_aslr(self.emu.arch.bits == 64, True)

    def LoadLibrary(self, emu: HyperEmu, ctx: Dict[str, Any], name: str) -> None:
        library_place = self._get_or_add_object(name)
        emu.return_from_function(library_place)

    def LoadLibraryA(self, emu: HyperEmu, ctx: Dict[str, Any]) -> None:
        # TODO make this code architecture generic
        lib_name = emu.mem.read_cstring(emu.regs.rcx)
        log.debug(f'LoadLibraryA called for {lib_name}')
        self.LoadLibrary(emu, ctx, lib_name)

    def LoadLibraryW(self, emu: HyperEmu, ctx: Dict[str, Any]) -> None:
        pass

    def GetProcAddress(self, emu: HyperEmu, ctx: Dict[str, Any]) -> None:
        # TODO make this code architecture generic
        func_name = emu.mem.read_cstring(emu.regs.rdx)
        func_address = self._get_function_address(emu.regs.rcx, func_name)
        if func_address is None:
            func_address = 1
        emu.return_from_function(func_address)

    def _fallback_get_function_address(self, object_name: str, function_name: str):
        if object_name in self._pe:
            return self._pe[object_name].function(function_name)
