import hyperstone as hs
from hyperstone import megastone as ms
from hyperstone.plugins.loaders import PELoaderInfo
from hyperstone.plugins.hooks import FunctionNullsubInfo, HookInfo


MAIN_PE = 'peloader/main.exe'

PE_LOADER = hs.plugins.loaders.PELoader(
    PELoaderInfo(MAIN_PE),
    PELoaderInfo('peloader/kernel32.dll'),
)


MAIN_BASE = (PE_LOADER @ MAIN_PE)

def symbol(resolver, name) -> int:
    return resolver.base + resolver.pe.get_section('.text').virtual_address + resolver.pe.get_symbol(name).value


SETTINGS = [
    PE_LOADER,

    hs.plugins.memory.mappers.InitializeSupportStack(),

    hs.plugins.hooks.Hook(
        HookInfo(
            'Anti ',
            0x0000000100061E68,
            None,
            lambda mu, _: (hs.log.info('AAAA'), hs.hooks.debug.print_registers(mu, 4))
        )
    ),

    hs.plugins.interfaces.PreparePlugin(lambda mu: prepare(mu)),

    hs.plugins.hooks.FunctionNullsub(
        FunctionNullsubInfo(symbol(PE_LOADER @ MAIN_PE, 'runtime.printlock')),
    FunctionNullsubInfo(symbol(PE_LOADER @ MAIN_PE, 'runtime.printunlock')),
),

    hs.plugins.runners.FunctionEntrypoint(symbol(PE_LOADER @ MAIN_PE, 'main.main'))
]


def prepare(emu: hs.HyperEmu):
    x28 = hs.hooks.support_malloc(emu, size=0x20)
    emu.mem.write_word(x28 + 0x10, emu.regs.sp + 0x10)
    emu.regs.x28 = x28


def main():
    hs.start(ms.ARCH_ARM64, SETTINGS)


if __name__ == '__main__':
    main()
