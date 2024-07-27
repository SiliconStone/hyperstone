from hyperstone.plugins.hooks.context import Context
from hyperstone.plugins.base import Plugin
from hyperstone.plugins.hooks import FakeObject
from hyperstone.plugins.loaders import PELoader, PELoaderInfo
from hyperstone.plugins.loaders.pe import calculate_aslr
from hyperstone.util.logger import log


# noinspection PyPep8Naming
# Windows function names
class FakeDll(FakeObject):
    """
    This plugin is the base `FakeObject` implementation for Windows-like object (See `PELoader`)
    It implements some basic `Kernel32` functions:
        KERNEL32.DLL!LoadLibraryA
        KERNEL32.DLL!LoadLibraryW
        KERNEL32.DLL!GetProcAddress
    These functions are implemented to fetch other fake or real DLLs.
    """
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
        if self._pe.has_fake_export(object_name) and function_name in self._pe.fake_export(object_name).functions:
            return self._pe.fake_export(object_name).functions[function_name]

        if object_name in self._pe:
            function_address = self._pe[object_name].function(
                function_name
            )
            if function_address:
                return function_address

    def _create_or_resolve_object_handle(self, name: str) -> int:
        if name not in self._pe:
            self._pe.interact(PELoaderInfo(name, fake=True))
        if name in self._pe:
            return self._pe[name].base
        elif self._pe.has_fake_export(name.lower()):
            return self._pe.fake_export(name.lower()).base
        else:
            return calculate_aslr(self.emu.arch.bits == 64, True)

    def LoadLibrary(self, ctx: Context, name: str) -> None:
        library_place = self._get_or_add_object(name)
        ctx.emu.return_from_function(library_place)

    def LoadLibraryA(self, ctx: Context) -> None:
        # TODO make this code architecture generic
        lib_name = ctx.emu.mem.read_cstring(ctx.emu.regs.rcx)
        log.debug(f'LoadLibraryA called for {lib_name}')
        self.LoadLibrary(ctx, lib_name)

    def LoadLibraryW(self, ctx: Context) -> None:
        pass

    def GetProcAddress(self, ctx: Context) -> None:
        # TODO make this code architecture generic
        func_name = ctx.emu.mem.read_cstring(ctx.emu.regs.rdx)
        func_address = self._get_function_address(ctx.emu.regs.rcx, func_name)
        if func_address is None:
            func_address = 1
        ctx.emu.return_from_function(func_address)

    def _fallback_get_function_address(self, object_name: str, function_name: str):
        if object_name in self._pe:
            return self._pe[object_name].function(function_name)
