from hyperstone.plugins.memory import SegmentInfo, RawStream, CodeStream, StreamMappingInfo
from hyperstone.plugins.hooks import HookType

import megastone as ms
import hyperstone as hs


OPCODE_SIZE = 4

SEGMENTS = hs.plugins.memory.MapSegment()

DATA_SEGMENT_ADDR = 0x04000000
EVIL_FUNCTION_ADDR = 0x08000100

SIMPLE_SETTINGS = [
    SEGMENTS,

    hs.plugins.memory.SetupMemory(support_base=0x10000000),  # We use the default support addr already

    hs.plugins.memory.MapStream(
        StreamMappingInfo(
            CodeStream(
                assembly=f'''
                PUSH    {{LR}}
                LDR     R1, ={DATA_SEGMENT_ADDR:#x}
                LDR     R0, [R1]
                BL      evil_function
                SUB     R0, #1
                @ TODO: Skip me, also fix the sub above
                bad:
                EOR     R0, R0
                B       bad
                BL      evil_function
                POP     {{PC}}
                
                .org {EVIL_FUNCTION_ADDR:#x}, 0
                evil_function:
                evil_loop:
                B       evil_loop
                BX      LR
                ''',
            ),
            SegmentInfo(
                name='test',
                address=0x08000000,
            )
        ),
        StreamMappingInfo(
            RawStream(
                data=b'AAAA'
            ),
            SegmentInfo(
                name='data',
                address=0x04000000,
                size=0x10,
            )
        )
    ),

    hs.plugins.hooks.Hooks(
        HookType(
            name='Skip bad',
            address=(SEGMENTS @ 'test').address + 5 * OPCODE_SIZE,
            return_address=(SEGMENTS @ 'test').address + 7 * OPCODE_SIZE,
            callback=lambda mu, _: (hs.hooks.ret(mu, mu.regs.r0 + 1), hs.hooks.debug_instructions_hook(mu))
        ),
    ),

    hs.plugins.hooks.FunctionStub(
        hs.plugins.hooks.StubInfo(
            EVIL_FUNCTION_ADDR
        )
    ),

    hs.plugins.runners.FunctionEntrypoint(0x08000000),
]


if __name__ == '__main__':
    emu = hs.start(ms.ARCH_ARM, SIMPLE_SETTINGS)
    hs.hooks.debug.print_registers(emu)
    hs.log.success(f'Retval {emu.regs.r0=:08X}')  # TODO: debug last opc
