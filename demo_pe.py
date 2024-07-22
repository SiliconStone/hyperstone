import hyperstone as hs
from hyperstone import megastone as ms
from hyperstone.plugins.loaders import PELoaderInfo


MAIN_PE = 'peloader/main.exe'

PE_LOADER = hs.plugins.loaders.PELoader()
MAIN_BASE = (PE_LOADER @ MAIN_PE)


SETTINGS = [
    PE_LOADER(
        PELoaderInfo(MAIN_PE, prefer_aslr=True),
        PELoaderInfo('peloader/FooBar.dll', prefer_aslr=True)
    ),

    hs.plugins.memory.InitializeSupportStack(),

    hs.plugins.memory.EnforceMemory(),
    hs.plugins.hooks.CallTrace(),

    hs.plugins.runners.FunctionEntrypoint(MAIN_BASE.entrypoint)
    # hs.plugins.runners.GDBServer()  # Try me!
]


def main():
    hs.start(ms.ARCH_X86_64, SETTINGS)


if __name__ == '__main__':
    main()
