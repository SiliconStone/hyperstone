import hyperstone as hs
from hyperstone import megastone as ms
from hyperstone.plugins.loaders import PELoaderInfo


MAIN_PE = 'peloader/main.exe'

PE_LOADER = hs.plugins.loaders.PELoader()
MAIN_BASE = (PE_LOADER @ MAIN_PE)


SETTINGS = [
    PE_LOADER(
        PELoaderInfo(MAIN_PE),
        PELoaderInfo('peloader/FooBar.dll')
    ),

    hs.plugins.memory.mappers.InitializeSupportStack(),

    # Comment/Uncomment this line to see how hyperstone behaves with PE
    hs.plugins.memory.EnforceMemory(),

    # On small PEs, this hopefully will point at an illegal X address (.rdata)
    hs.plugins.runners.FunctionEntrypoint(MAIN_BASE.entrypoint + 0x101C)
]


def main():
    hs.start(ms.ARCH_X86_64, SETTINGS)


if __name__ == '__main__':
    main()
