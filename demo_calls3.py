from hyperstone.plugins.memory import StreamMapperInfo, CodeStream, SegmentInfo
from hyperstone.plugins.hooks import HookInfo
from hyperstone import megastone as ms
import hyperstone as hs

class Settings(hs.Settings):
    _STACK = hs.plugins.memory.InitializeSupportStack()

    Entry = 0x08_00_00_00
    FuncAddr = 0x08_00_01_00

    CODE = hs.plugins.memory.StreamMapper(
        StreamMapperInfo(
            CodeStream(f'''
                push    33
                push    22
                push    11
                call    testfunc
                add     esp, 12
                ret
                
            .org {FuncAddr:#x}, 0
            testfunc:
                int 3
            '''),
            SegmentInfo(
                name='.text',
                address=Entry,
            )
        )
    )

    @staticmethod
    def teststuff(ctx: hs.Context, a, b, c):
        hs.log.success(f'{a=} {b=} {c=}')
        ctx.emu.return_from_function()

    HOOKS = hs.plugins.hooks.Hook(
        HookInfo(
            'testfunc',
            FuncAddr,
            callback=hs.calls.CDecl(teststuff),
        )
    )

    ENTRYPOINT = hs.plugins.runners.FunctionEntrypoint(Entry)


def main():
    hs.start(ms.ARCH_X86, Settings)


if __name__ == '__main__':
    main()
