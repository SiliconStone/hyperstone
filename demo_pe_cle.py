import hyperstone as hs
from hyperstone import megastone as ms
from hyperstone.plugins.loaders import CLELoaderInfo


MAIN_PE = 'peloader/main.exe'
LOADER = hs.plugins.loaders.cle.CLELoader()

SETTINGS = [
    LOADER(
        CLELoaderInfo(
            MAIN_PE,
        )
    ),

    hs.plugins.memory.mappers.InitializeSupportStack(),

    # hs.plugins.memory.EnforceMemory(),

    hs.plugins.runners.FunctionEntrypoint(LOADER.loaded.main_object.entry)
]


def main():
    hs.start(ms.ARCH_X86_64, SETTINGS)


if __name__ == '__main__':
    main()
