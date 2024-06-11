"""
ELF Loader
"""
from dataclasses import dataclass

import lief
from lief.ELF import E_TYPE
from lief.ELF import SEGMENT_TYPES

from hyperstone.plugins.base import Plugin


@dataclass(frozen=True)
class ELFInfo:
    path: str


class ELFLoader(Plugin):
    _INTERACT_TYPE = ELFInfo

    def __init__(self, *files: ELFInfo):
        super().__init__(*files)

    def _prepare(self):
        pass

    def _handle(self, obj: ELFInfo):
        binary: lief.ELF.Binary = lief.ELF.parse(obj.path)
        # Getting the e_type
        e_type = binary.header.file_type
        if e_type == E_TYPE.RELOCATABLE:
            # kernel object?
            pass
        if e_type == E_TYPE.DYNAMIC:
            # Shared object maybe load with ld?
            pass
        if e_type == E_TYPE.EXECUTABLE:
            # Executable
            self.load_executable(binary)

    def load_executable(self, binary: lief.ELF.Binary):
        segments = [segment
                         for segment in binary.segments if
                         segment.type == SEGMENT_TYPES.LOAD]
        segments = sorted(segments, key=lambda seg: seg.virtual_address)
        for seg in segments:
            # Virtual size is already aligned.
            # mmap seg.virtual_size
            pass
