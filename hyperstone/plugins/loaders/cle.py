from typing import Callable, Optional, Tuple, Union

import cle
import megastone as ms

from hyperstone.plugins.memory import (StreamMapper, StreamMapperInfo, LazyStream, Segment, SegmentInfo,
                                       EnforceMemory, EnforceMemoryInfo)
from hyperstone.plugins.base import Plugin
from hyperstone.util import log, LazyResolver

CLELoaderInfo = cle.Loader


class CLELoader(Plugin):
    _INTERACT_TYPE = CLELoaderInfo
    CLE_SECTION_TEMPLATE = 'CLE.SECTION."{binary}"."{section}"'
    CLE_SEGMENT_TEMPLATE = 'CLE.SEGMENT."{binary}"."#{segment}"'

    def __init__(self, *args: CLELoaderInfo):
        super().__init__(*args)
        self._first_cle: Optional[CLELoaderInfo] = None
        self._security_strategy = CLELoader._security_megastone
        self._segment_plugin: Optional[Segment] = None
        self._mapper_plugin: Optional[StreamMapper] = None

    def interact(self, *objs: CLELoaderInfo):
        for _ in objs:
            if len(self.get_interacted) == 0:
                self._first_cle = objs[0]
            else:
                log.warning('CLELoader might won\'t work with more than one interaction')
            break

        super().interact(*objs)

    def _prepare(self):
        self._mapper_plugin = Plugin.require(StreamMapper, self.emu)
        self._segment_plugin = Plugin.require(Segment, self.emu)

        for _ in Plugin.get_all_loaded(EnforceMemory, self.emu):
            log.debug(f'Using EnforceMemory strategy.')
            self._security_strategy = self._security_enforce

    @property
    def loaded(self) -> CLELoaderInfo:
        return self._first_cle

    def _handle(self, obj: CLELoaderInfo):
        for binary in obj.all_objects:
            # So, our goal is to map just the sections
            # Of course, an ELF is usually mapped fully while a PE is only mapped by the headers
            # And PELoader supports it.
            # However,
            log.info(f'Loading {binary}')
            binary.relocate()

            if binary.sections:
                self._map_sections(binary, obj)
            elif binary.segments:
                self._map_segments(binary, obj)

    def _map_segments(self, binary: cle.Backend, loader: CLELoaderInfo):
        for i, segment in enumerate(binary.segments):
            segment_name = CLELoader.CLE_SEGMENT_TEMPLATE.format(binary=binary, segment=i)
            self._map_segment(loader, segment, segment_name)

    @staticmethod
    def _security_megastone(section: cle.Segment) -> Tuple[ms.AccessType, Optional[Callable[[str], None]]]:
        perms = ms.AccessType.NONE
        perms |= ms.AccessType.R if section.is_readable else ms.AccessType.NONE
        perms |= ms.AccessType.W if section.is_writable else ms.AccessType.NONE
        perms |= ms.AccessType.X if section.is_executable else ms.AccessType.NONE

        return perms, None

    def _security_enforce(self, section: cle.Segment) -> [ms.AccessType, Optional[Callable[[str], None]]]:
        def callback(section_name: str):
            self._mapper_plugin.prepare(self.emu)

            enforce_plugin = Plugin.get_loaded(EnforceMemory, self.emu)
            enforce_plugin.interact(EnforceMemoryInfo(
                self._segment_plugin.mapped(section_name),
                CLELoader._security_megastone(section)[0]
            ))

        return ms.AccessType.RWX, callback

    def _map_sections(self, binary: cle.Backend, loader: CLELoaderInfo):
        for section in binary.sections:
            if section.vaddr == 0:
                log.warning(f'Skipping bad section {section.name} ({section}) (vaddr is 0)')
                continue

            section_name = CLELoader.CLE_SECTION_TEMPLATE.format(binary=binary.binary_basename, section=section.name)
            log.debug(f'Loading section {section}')
            self._map_segment(loader, section, section_name)

    def _map_segment(self, loader: CLELoaderInfo, segment: Union[cle.Segment, cle.Section], section_name: str):
        perms, callback = self._security_strategy(segment)

        log.debug(f'Mapping {section_name} [{perms}]')

        self._mapper_plugin.interact(
            StreamMapperInfo(
                LazyStream(
                    LazyResolver(loader).memory.load(
                        segment.min_addr,
                        segment.memsize
                    )
                ),
                SegmentInfo(
                    section_name,
                    segment.min_addr,
                    segment.memsize,
                    perms
                )
            )
        )

        if callback is not None:
            callback(section_name)
