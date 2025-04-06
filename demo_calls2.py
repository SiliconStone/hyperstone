from hyperstone.plugins.memory import StreamMapperInfo, CodeStream, SegmentInfo
from hyperstone.plugins.interfaces import ExportFunctionInfo
from hyperstone import megastone as ms
import hyperstone as hs

class Settings(hs.Settings):
    _STACK = hs.plugins.memory.InitializeSupportStack()

    FuncAddr = 0x08_00_00_00

    CODE = hs.plugins.memory.StreamMapper(
        StreamMapperInfo(
            CodeStream('''
            myfunc:
                push    ebp
                mov     ebp, esp
                mov     eax, [ebp + 8]
                mov     ebx, [ebp + 12]
                mov     ecx, [ebp + 16]
                pop     ebp
                ret
            '''),
            SegmentInfo(
                name='.text',
                address=FuncAddr,
            )
        )
    )

    FUNCTIONS = hs.plugins.interfaces.ExportFunction(
        ExportFunctionInfo('myfunc', FuncAddr, hs.calls.CDecl)
    )

def main():
    emu, _ = hs.prepare(ms.ARCH_X86, Settings)
    Settings.FUNCTIONS['myfunc'](0xaa, 0xbb, 0xcc)
    hs.hooks.print_registers(emu)
    # eax -> 0xaa, ebx -> 0xbb, ecx -> 0xcc


if __name__ == '__main__':
    main()
