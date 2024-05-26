from hyperstone.plugins.loaders import PELoaderInfo
from hyperstone.plugins.hooks import HookInfo
from hyperstone import megastone as ms
import hyperstone as hs


class Settings(hs.Settings):
    STACK = hs.plugins.memory.InitializeSupportStack()
    SEGMENTS = hs.plugins.memory.Segment()

    LOADER = hs.plugins.loaders.PELoader(
        PELoaderInfo("peloader/upx.exe", map_header_rwx=True),
        dll_search_paths=["%windir%\\system32"],
    )

    FAKE_DLL = hs.plugins.hooks.FakeDll()

    HOOKS = hs.plugins.hooks.Hook()

    ENTRY = hs.plugins.runners.FunctionEntrypoint(
        LOADER.query("peloader/upx.exe").entrypoint
    )


def main():
    """
    This demo isn't 100%, but it somewhat works.
    """
    emu = hs.start(arch=ms.ARCH_X86_64, settings=Settings)
    segment_plugin = hs.Plugin.get_loaded(hs.plugins.memory.Segment, emu)

    upx0 = segment_plugin['PE.SECTION."peloader/upx.exe"."UPX0"']
    upx1 = segment_plugin['PE.SECTION."peloader/upx.exe"."UPX1"']
    rsrc = segment_plugin['PE.SECTION."peloader/upx.exe".".rsrc"']
    header = segment_plugin['PE.HEADER."peloader/upx.exe"']
    emu.mem.dump_to_file(upx0.address, upx0.size, 'upx0')
    emu.mem.dump_to_file(upx1.address, upx1.size, 'upx1')
    emu.mem.dump_to_file(rsrc.address, rsrc.size, 'rsrc')
    emu.mem.dump_to_file(header.address, header.size, 'header')


if __name__ == "__main__":
    main()
