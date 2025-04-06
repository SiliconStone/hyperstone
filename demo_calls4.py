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
                push    11
                push    22
                push    33
                call    testfunc
                ret
                
            .org {FuncAddr:#x}, 0
            testfunc:
                int     3
                ret     12
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
        # We are returning from the function, as per stdcall, we need to do some registers cleanup!!
        # We should use StdCallCleanup in order to allow this behaviour
        ctx.emu.return_from_function()

    @staticmethod
    def just_inspecting(_: hs.Context, a, b, c):
        # Since we don't return here (and just check the vars), we can use StdCall
        hs.log.success(f'{a=} {b=} {c=}')

    HOOKS = hs.plugins.hooks.Hook(
        HookInfo(
            'just checking',
            FuncAddr,
            callback=hs.calls.StdCall(just_inspecting),
        ),
        HookInfo(
            'testfunc',
            FuncAddr,
            callback=hs.calls.StdCallCleanup(teststuff),
        )
    )

    ENTRYPOINT = hs.plugins.runners.FunctionEntrypoint(Entry)


def main():
    hs.start(ms.ARCH_X86, Settings)


if __name__ == '__main__':
    main()
