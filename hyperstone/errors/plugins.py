from hyperstone.errors.base import HyperstoneError


class HyperstonePluginError(HyperstoneError):
    pass


class HSPluginInteractNotReady(HyperstonePluginError):
    pass
