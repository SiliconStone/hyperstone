class HyperstoneError(Exception):
    pass


class HyperstonePluginError(HyperstoneError):
    pass


class HSPluginInteractNotReadyError(HyperstonePluginError):
    pass


class HSPluginConflictError(HyperstonePluginError):
    pass


class HSPluginNotFoundError(HyperstonePluginError):
    pass