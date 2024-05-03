import megastone as ms

import hyperstone as hs
from hyperstone.plugins.memory import SegmentInfo, StreamMapperInfo, CodeStream, RawStream, EnforceMemoryInfo

OPCODE_SIZE = 4

SEGMENTS = hs.plugins.memory.Segment()

SIMPLE_SETTINGS = [
    SEGMENTS,

    hs.plugins.memory.StreamMapper(
        StreamMapperInfo(
            CodeStream(
                assembly='''
                LDR     R1, =0x04000000
                LDR     R0, [R1]
                NOP
                NOP
                NOP
                BX      LR
                ''',
            ),
            SegmentInfo(
                name='test',
                address=0x08000000,
                size=0x400,
            )
        ),
        StreamMapperInfo(
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

    hs.plugins.memory.EnforceMemory(
        EnforceMemoryInfo(
            ms.AddressRange(
                0x04000000,
                4,
            ),
            ms.AccessType.NONE
        )
    ),

    hs.plugins.runners.FunctionEntrypoint(0x08000000),
]

if __name__ == '__main__':
    try:
        emu = hs.start(ms.ARCH_ARM, SIMPLE_SETTINGS)
    except hs.exceptions.HSRuntimeBadAccess:
        hs.log.warning(f'Ignored exception')
