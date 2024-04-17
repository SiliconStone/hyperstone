from hyperstone.hooks import context, debug, registers
from hyperstone.hooks.context import ctx_init
from hyperstone.hooks.debug import debug_instructions_hook, print_registers
from hyperstone.hooks.memory import support_malloc
from hyperstone.hooks.registers import args, ok, ret, set_retval

__all__ = [
    # Categories
    'context',
    'debug',
    'memory',
    'registers',

    # Context
    'ctx_init',

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