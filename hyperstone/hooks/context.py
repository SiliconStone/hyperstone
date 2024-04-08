from typing import Any, Dict

ONLY_HAS_GLOBALS = 1


def ctx_init(ctx: Dict[str, Any], default: Dict[str, Any]) -> Dict[str, Any]:
    if ONLY_HAS_GLOBALS == len(ctx):
        ctx.update(default)

    return ctx
