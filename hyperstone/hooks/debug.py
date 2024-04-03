from hyperstone.util.logger import log
from hyperstone.emulator import HyperEmu


def debug_instructions_hook(emu: HyperEmu):
    log.info('Adding debug instructions hook')
    emu.add_code_hook(lambda e: log.debug(f'{e.get_curr_insn()} - {hex(e.pc)}'))
