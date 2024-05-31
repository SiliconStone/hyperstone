class HyperstoneError(Exception):
    pass


class HyperstoneRuntimeError(HyperstoneError):
    pass


class HyperstoneHooksError(HyperstoneError):
    pass


class HyperstonePluginError(HyperstoneError):
    pass


class HSRuntimeBadAccess(HyperstoneRuntimeError):
    pass


class HSHookBadParameters(HyperstoneHooksError):
    pass


class HSHookBadState(HyperstoneHooksError):
    pass


class HSHookAlreadyRemovedError(HyperstoneHooksError):
    pass


class HSPluginInteractNotReadyError(HyperstonePluginError):
    pass


class HSPluginInteractionError(HyperstonePluginError):
    pass


class HSPluginConflictError(HyperstonePluginError):
    pass


class HSPluginBadStateError(HyperstonePluginError):
    pass


class HSPluginNotFoundError(HyperstonePluginError):
    pass
