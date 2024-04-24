import hyperstone as hs
from hyperstone import megastone as ms
from hyperstone.plugins.loaders import PELoaderInfo


PE_LOADER = hs.plugins.loaders.PELoader(
    PELoaderInfo('peloader/main.exe'),
    PELoaderInfo('peloader/kernel32.dll'),
)

SETTINGS = [
    PE_LOADER,

    hs.plugins.runners.FunctionEntrypoint((PE_LOADER @ 'peloader/main.exe').entrypoint)
]


def main():
    hs.start(ms.ARCH_ARM64, SETTINGS)


if __name__ == '__main__':
    main()
