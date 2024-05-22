from typing import Any, Dict
from hyperstone.util.logger import log
from hyperstone.emulator import HyperEmu
from hyperstone.plugins.base import Plugin
from hyperstone.plugins.hooks import FakeObject
from hyperstone.plugins.loaders import PELoader
from hyperstone.plugins.loaders.pe import calculate_aslr


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
        super()._prepare()

    def _resolve_export_fallback(self, object_name: str, function_name: str) -> int | None:
        if (
            object_name in self._pe._phantom_hooks
            and function_name in self._pe._phantom_hooks[object_name]
        ):
            return self._pe._phantom_hooks[object_name][function_name]

    def _create_or_resolve_object_handle(self, name: str) -> int:
        return calculate_aslr(self.emu.arch.bits == 64, True)

    def LoadLibrary(self, emu: HyperEmu, ctx: Dict[str, Any], name: str) -> None:
        library_place = self._get_or_add_object(name)
        emu.return_from_function(library_place)

    def LoadLibraryA(self, emu: HyperEmu, ctx: Dict[str, Any]) -> None:
        # TODO make this code architecture generic
        lib_name = emu.mem.read_cstring(emu.regs.rcx)
        log.debug(f"LoadLibraryA called for {lib_name}")
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
