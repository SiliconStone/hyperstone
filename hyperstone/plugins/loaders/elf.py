"""
ELF Loader
"""
from hyperstone.plugins.base import Plugin
from dataclasses import dataclass
@dataclass(frozen=True)
class ELFInfo:
    path: str

class ELFLoader(Plugin):
    _INTERACT_TYPE = ELFInfo

    def __init__(self, *files: ELFInfo):
        pass

    def _handle(self, obj: ELFInfo):
        pass

