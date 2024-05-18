from unicorn import UcError
from ctypes import ArgumentError

from hyperstone.util.formatting import tabbed_print
from hyperstone.emulator import HyperEmu
from hyperstone.util.logger import log


def debug_instructions_hook(emu: HyperEmu):
    log.info('Adding debug instructions hook')
    emu.add_code_hook(lambda e: log.debug(f'{e.get_curr_insn()} - {hex(e.pc)}'))


def print_registers(emu: HyperEmu, amount: int = 4):
    def get_one():
        for i, reg in enumerate(emu.arch.regs):
            try:
                data = f'{emu.regs.read(reg):08X}'
            except (UcError, ArgumentError, TypeError):
                data = '????????'

            yield {'REGISTER': reg.name.upper(), 'VALUE': data}

    tabbed_print(header=['REGISTER', 'VALUE'], body=get_one(), amount_per_line=amount)
