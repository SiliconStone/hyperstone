"""
ELF Loader
"""
from hyperstone import HyperEmu
from hyperstone.plugins.base import Plugin
from dataclasses import dataclass
@dataclass(frozen=True)
class ELFInfo:
    path: str

class ELFLoader(Plugin):
    _INTERACT_TYPE = ELFInfo

    def __init__(self, *files: ELFInfo):
        super().__init__(*files)
    def prepare(self, emu: HyperEmu):
        pass

    def _handle(self, obj: ELFInfo):
        pass

