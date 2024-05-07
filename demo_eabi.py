from hyperstone.hooks.registers import eabi
from hyperstone.plugins.memory.mappers import StreamMapperInfo, SegmentInfo
from hyperstone.plugins.memory.streams import CodeStream
from hyperstone.plugins.hooks import HookInfo, FunctionNullsubInfo
from hyperstone import megastone as ms

import hyperstone as hs


def debug_malloc1(emu: hs.HyperEmu, size: int):
    hs.log.info(f'malloc1 {size:#x}')
    hs.hooks.set_retval(emu, emu.mem.allocate(size).address)


def debug_malloc2(emu: hs.HyperEmu, size: int, name_int: int = 0):
    names_list = [
        '[malloc2 heap]',
        '[malloc2 heap - Alt]',
        '[Cool dev heap]',
    ]
    if name_int > len(names_list):
        name = f'[Custom - {name_int}]'
    else:
        name = names_list[name_int]
    hs.log.info(f'malloc2 {size:#x} {name}')
    hs.hooks.set_retval(emu, emu.mem.allocate(size, name).address)


class Settings(hs.Settings):
    _stack = hs.plugins.memory.InitializeSupportStack()
    CONSTS = hs.plugins.consts.ARMConsts()

    BASE = 0x04000000

    MALLOC1__R0 = BASE + 0x100 * 1
    MALLOC2__R0 = BASE + 0x100 * 2
    MALLOC1__R1 = BASE + 0x100 * 3
    MALLOC2__R1 = BASE + 0x100 * 4
    MALLOC2__R0__NAME_R1 = BASE + 0x100 * 5
    MALLOC2__R0__NAME_USER = BASE + 0x100 * 6

    FUNCTIONS_NULLSUB = [MALLOC1__R0, MALLOC2__R0, MALLOC1__R1, MALLOC2__R1, MALLOC2__R0__NAME_R1,
                         MALLOC2__R0__NAME_USER]

    MAIN_CODE = hs.plugins.memory.StreamMapper(
        StreamMapperInfo(
            CodeStream(
                f'''
                PUSH    {{LR}}
                
                @ Stubbing MALLOC1__R0 with malloc1()
                MOV     R0, 0x100
                BL      MALLOC1__R0
                
                @ Stubbing MALLOC2__R0 with malloc2()
                MOV     R0, 0x200
                BL      MALLOC2__R0
                
                @ Alternative API for MALLOC1__R1 via malloc1()
                MOV     R0, 0xdead
                MOV     R1, 0x300
                BL      MALLOC1__R1
                
                @ Alternative API for MALLOC2__R1 via malloc2()
                MOV     R0, 0xdead
                MOV     R1, 0x400
                BL      MALLOC2__R1
                
                @ Now we also accept a name argument from emu, which is a default arg in hyperstone
                MOV     R0, 0x500
                MOV     R1, 69
                BL      MALLOC2__R0__NAME_R1
                
                @ At last, in this function we pull R0 but also supply the name from our hook def
                MOV     R0, 0x600
                BL      MALLOC2__R0__NAME_USER
                
            halt:
                NOP
                NOP
                NOP
                POP     {{PC}}
                
            .org {MALLOC1__R0:#x}, 0
            MALLOC1__R0:
                SVC     0
            .org {MALLOC2__R0:#x}, 0
            MALLOC2__R0:
                SVC     0
            .org {MALLOC1__R1:#x}, 0
            MALLOC1__R1:
                SVC     0
            .org {MALLOC2__R1:#x}, 0
            MALLOC2__R1:
                SVC     0
            .org {MALLOC2__R0__NAME_R1:#x}, 0
            MALLOC2__R0__NAME_R1:
                SVC     0
            .org {MALLOC2__R0__NAME_USER:#x}, 0
            MALLOC2__R0__NAME_USER:
                SVC     0
                '''
            ),
            SegmentInfo(
                'CODE',
                BASE
            )
        )
    )

    HOOKS = hs.plugins.hooks.Hook(
        HookInfo(
            'MALLOC1__R0',
            MALLOC1__R0,
            None,
            lambda mu, _: eabi(mu, debug_malloc1)
        ),
        HookInfo(
            'MALLOC2__R0',
            MALLOC2__R0,
            None,
            lambda mu, _: eabi(mu, debug_malloc2)
        ),
        HookInfo(
            'MALLOC1__R1',
            MALLOC1__R1,
            None,
            lambda mu, _: debug_malloc1(mu, mu.regs.r1)
        ),
        HookInfo(
            'MALLOC2__R1',
            MALLOC2__R1,
            None,
            lambda mu, _: debug_malloc2(mu, mu.regs.r1, name_int=1)  # Alt
        ),
        HookInfo(
            'MALLOC2__R0__NAME_R1',
            MALLOC2__R0__NAME_R1,
            None,
            lambda mu, _: eabi(mu, debug_malloc2, respect_defaults=False)
        ),
        HookInfo(
            'MALLOC2__R0__NAME_USER',
            MALLOC2__R0__NAME_USER,
            None,
            lambda mu, _: eabi(mu, debug_malloc2, name_int=2)  # Dev
        ),
    )

    _STUB_HOOKCALLS = hs.plugins.hooks.FunctionNullsub(
        *(FunctionNullsubInfo(address) for address in FUNCTIONS_NULLSUB)
    )

    RUN_BASE = hs.plugins.runners.FunctionEntrypoint(BASE)


def main():
    """
    This example showcases the eabi() functionality in hooks.
    eabi() allows call a hyperstone.hooks.<function> utility callback with the correct calling convention
    (by getting parameters from registers).

    This example also showcases a Settings class, which might be more organised to some users.
    In here, we use the Settings class to keep track of custom offsets (which we might want to showcase when
        calling print(Settings) )
    """
    print(Settings)
    hs.start(ms.ARCH_ARM, Settings)


if __name__ == '__main__':
    main()
