from hyperstone.plugins.hooks.base import Hook, HookInfo, ActiveHook, HyperstoneCallback
from hyperstone.plugins.hooks.call_trace import CallTrace
from hyperstone.plugins.hooks.nullsub import FunctionNullsub, FunctionNullsubInfo
from hyperstone.plugins.hooks.virtual_registry import VirtualRegistry, VirtualRegistryInfo, RegistryAction
from hyperstone.plugins.hooks.fake_object import FakeObject
from hyperstone.plugins.hooks.fake_dll import FakeDll


__all__ = [
    'Hook',
    'HookInfo',
    'ActiveHook',

    'HyperstoneCallback',

    'CallTrace',

    'FunctionNullsub',
    'FunctionNullsubInfo',

    'VirtualRegistry',
    'VirtualRegistryInfo',
    'RegistryAction',

    'FakeObject',
    'FakeDll',
]
