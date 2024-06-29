from hyperstone.hooks import debug, registers
from hyperstone.hooks.debug import debug_instructions_hook, print_registers
from hyperstone.hooks.memory import support_malloc
from hyperstone.hooks.registers import args, ok, ret, set_retval

__all__ = [
    # Categories
    'debug',
    'memory',
    'registers',

    # Debug
    'debug_instructions_hook',
    'print_registers',

    # Memory
    'support_malloc',

    # Registers
    'args',
    'ok',
    'ret',
    'set_retval',
]
