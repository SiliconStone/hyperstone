import megastone as ms

import hyperstone as hs
import hyperstone.plugins.memory.map_code
import hyperstone.plugins.memory.map_raw
from hyperstone import HyperEmu
from hyperstone.plugins.memory import SegmentInfo, CodeSegment, CodeStream, RawSegment, RawStream
from hyperstone.plugins.hooks import HookType

OPCODE_SIZE = 4

SEGMENTS = hs.plugins.memory.map_segment.MapSegment()

SIMPLE_SETTINGS = [
    SEGMENTS,

    hyperstone.plugins.memory.map_code.MapCode(
        CodeSegment(
            CodeStream(
                assembly='''
                LDR     R1, =0x04000000
                LDR     R0, [R1]
                SUB     R0, #1
                @ TODO: Skip me, also fix the sub above
                bad:
                EOR     R0, R0
                B       bad
                BX      LR
                ''',
            ),
            SegmentInfo(
                name='test',
                address=0x08000000,
                size=0x400,
            )
        )
    ),

    hyperstone.plugins.memory.map_raw.MapRaw(
        RawSegment(
            RawStream(
                data=b'AAAA'
            ),
            SegmentInfo(
                name='data',
                address=0x04000000,
                size=0x400,
            )
        )
    ),

    hs.plugins.hooks.Hooks(
        HookType(
            name='Skip bad',
            address=(SEGMENTS @ 'test').address + 3 * OPCODE_SIZE,
            return_address=(SEGMENTS @ 'test').address + 5 * OPCODE_SIZE,
            callback=lambda mu, _: (hs.hooks.ret(mu, mu.regs.r0 + 1), hs.hooks.debug_instructions_hook(mu))
        ),
    ),

    hs.plugins.runners.FunctionEntrypoint(0x08000000),
]


if __name__ == '__main__':
    emu = hs.start(ms.ARCH_ARM, SIMPLE_SETTINGS)
    hs.log.success(f'Retval {emu.regs.r0=:08X}')
