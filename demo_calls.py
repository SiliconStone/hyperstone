from hyperstone.plugins.memory.mappers import StreamMapperInfo, SegmentInfo
from hyperstone.plugins.memory.streams import CodeStream
from hyperstone.plugins.hooks import HookInfo, FunctionNullsubInfo
from hyperstone import megastone as ms

import hyperstone as hs


def debug_malloc1(ctx: hs.Context, size: int):
    print('aaaa')
    hs.log.info(f'malloc1 {size:#x}')
    hs.hooks.set_retval(ctx.emu, ctx.emu.mem.allocate(size).address)


def debug_malloc2(ctx: hs.Context, size: int, name_int: int = 0):
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
    hs.hooks.set_retval(ctx.emu, ctx.emu.mem.allocate(size, name).address)


def debug_malloc3(ctx: hs.DictContext, size: int, checksum: int):
    if checksum != 1337:
        hs.log.error('malloc3 checksum mismatch')
        return

    name = ctx['name']
    hs.log.info(f'malloc3 {size:#x} {name}')
    hs.log.debug(f'malloc3 context - {ctx}')
    hs.hooks.set_retval(ctx.emu, ctx.emu.mem.allocate(size, name).address)


class Settings(hs.Settings):
    _stack = hs.plugins.memory.InitializeSupportStack()

    BASE = 0x04000000

    MALLOC1__R0 = BASE + 0x100 * 1
    MALLOC2__R0 = BASE + 0x100 * 2
    MALLOC1__R1 = BASE + 0x100 * 3
    MALLOC2__R1 = BASE + 0x100 * 4
    MALLOC2__R0__NAME_R1 = BASE + 0x100 * 5
    MALLOC2__R0__NAME_USER = BASE + 0x100 * 6
    MALLOC3__R0__CTX = BASE + 0x100 * 7

    FUNCTIONS_NULLSUB = [MALLOC1__R0, MALLOC2__R0, MALLOC1__R1, MALLOC2__R1, MALLOC2__R0__NAME_R1,
                         MALLOC2__R0__NAME_USER, MALLOC3__R0__CTX]

    _DBG = hs.plugins.hooks.CallTrace()

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
                
                @ Bonus, pass context
                MOV     R0, 0x700
                BL      MALLOC3__R0__CTX

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
            .org {MALLOC3__R0__CTX:#x}, 0
            MALLOC3__R0__CTX:
                SVC     0
                '''
            ),
            SegmentInfo(
                'CODE',
                BASE
            )
        )
    )

    _REGS = ms.ARCH_ARM.regs
    ARM_CONV = hs.calls.RegisterCall(
        _REGS.r0,
        _REGS.r1,
        _REGS.r2,
        _REGS.r3,
    )
    ALT_CONV = hs.calls.RegisterCall(
        _REGS.r1,
        _REGS.r2,
        _REGS.r3,
    )

    HOOKS = hs.plugins.hooks.Hook(
        HookInfo(
            'MALLOC1__R0',
            MALLOC1__R0,
            callback=ARM_CONV(debug_malloc1)
        ),
        HookInfo(
            'MALLOC2__R0',
            MALLOC2__R0,
            callback=ARM_CONV(debug_malloc2)
        ),
        HookInfo(
            'MALLOC1__R1',
            MALLOC1__R1,
            callback=ALT_CONV(debug_malloc1)
        ),
        HookInfo(
            'MALLOC2__R1',
            MALLOC2__R1,
            callback=ALT_CONV(debug_malloc2, name_int=1)  # Alt
        ),
        HookInfo(
            'MALLOC2__R0__NAME_R1',
            MALLOC2__R0__NAME_R1,
            callback=ARM_CONV(lambda mu, size, name: debug_malloc2(mu, size, name_int=name))
        ),
        HookInfo(
            'MALLOC2__R0__NAME_USER',
            MALLOC2__R0__NAME_USER,
            callback=ARM_CONV(debug_malloc2, name_int=2)  # User
        ),
        HookInfo(
            'MALLOC3__R0__CTX',
            MALLOC3__R0__CTX,
            callback=ARM_CONV(debug_malloc3, 1337),  # Checksum arg
            ctx=hs.DictContext(name='[Heap with context!]')
        )
    )

    _STUB_HOOKCALLS = hs.plugins.hooks.FunctionNullsub(
        *(FunctionNullsubInfo(address) for address in FUNCTIONS_NULLSUB)
    )

    RUN_BASE = hs.plugins.runners.FunctionEntrypoint(BASE)


def main():
    """
    This example is a direct comparison to the eabi() example and serves as a possible replacement for eabi()
    It shows how to construct 2 custom calling conventions, use them with *args and **kwargs, lambdas and more!
    It also shows how to call functions with context.
    Note that by default Hyperstone's Hook plugin always passes the emulator and a designated context object,
    This is just an abstraction layer above it.
    """
    hs.start(ms.ARCH_ARM, Settings)


if __name__ == '__main__':
    main()
