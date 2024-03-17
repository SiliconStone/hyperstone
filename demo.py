import megastone as ms

import hyperstone as hs
import hyperstone.plugins.memory.map_code
import hyperstone.plugins.memory.map_raw
from hyperstone.plugins.memory import SegmentInfo, CodeSegment, CodeStream, RawSegment, RawStream

SIMPLE_SETTINGS = [
    hyperstone.plugins.memory.map_code.MapCode(
        CodeSegment(
            CodeStream(
                assembly='''
                LDR     R1, =0x04000000
                LDR     R0, [R1]
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

    hs.plugins.emulation.FunctionEntrypoint(0x08000000),
]

if __name__ == '__main__':
    emu = hs.start(ms.ARCH_ARM, SIMPLE_SETTINGS)
    hs.log.success(f'Retval {emu.regs.r0=:08X}')
