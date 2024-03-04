from hyperstone.errors.base import HyperstoneError


class HyperstonePluginError(HyperstoneError):
    ...


class HSPluginInteractNotReady(HyperstonePluginError):
    ...
