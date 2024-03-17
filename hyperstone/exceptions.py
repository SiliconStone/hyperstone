class HyperstoneError(Exception):
    pass


class HyperstonePluginError(HyperstoneError):
    pass


class HSPluginInteractNotReadyError(HyperstonePluginError):
    pass
