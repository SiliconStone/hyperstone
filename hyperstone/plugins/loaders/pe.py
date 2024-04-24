from dataclasses import dataclass, field
from typing import Optional, Dict

import random
import lief.PE
import megastone as ms

from hyperstone.plugins.base import Plugin
from hyperstone.plugins.memory import Segment, SegmentInfo, StreamMapper, StreamMapperInfo, FileStream, RawStream
from hyperstone.exceptions import HSPluginInteractNotReadyError, HSPluginBadStateError
from hyperstone.util.logger import log


FileNameType = str


@dataclass(frozen=True)
class PELoaderInfo:
    """
    Represents a PE file that we want to map
    :var file: The path to a file we want to load
    :var base: An optional base address for the PE file
    :var prefer_aslr: Should we try to map with ASLR enabled?
    """
    file: FileNameType
    base: Optional[int] = None
    prefer_aslr: bool = False


@dataclass(frozen=True)
class LoadedPEInfo:
    info: PELoaderInfo
    base: int


def calculate_aslr(high_entropy: bool, is_dll: bool) -> int:
    """
    Suggest an ASLR'd base

    :param high_entropy: Related to the Char in OptionalHeader, means we support >4GB 64bit ASLR
    :param is_dll: DLLs have higher ASLR range
    :return: A proposed base (with ASLR)

    DLL images based above 4 GB: 19 bits of entropy (1 in 524,288 chance of guessing correctly)
    DLL images based below 4 GB: 14 bits of entropy (1 in 16,384 chance of guessing correctly).
    EXE images based above 4 GB: 17 bits of entropy (1 in 131,072 chance of guessing correctly).
    EXE images based below 4 GB: 8 bits of entropy (1 in 256 chance of guessing correctly).

    K - Kernel
    E - EXE
    D - DLL
    X - Cannot randomise
    0 - Usually 0
    1 - Usually 1 (For DLLs)

    Random for 32 bit:
    PDP - PDE - PTE - Offset
    00-00 0000 000-0 0000 0000 - 0000 0000 0000
    KK-DD DDDD EEE-E EEEE 0000 - XXXX XXXX XXXX

    Random for 64 bit:
    Sign Extend - PML4 - PDP - PDE - PTE - Offset
    0000 0000 0000 0000 - 0000 0000 0-000 0000
    KKKK KKKK KKKK KKKK - K111 1111 1-111 1DDE

    00-00 0000 000-0 0000 0000 - 0000 0000 0000
    EE-EE EEEE EEE-E EEEE 0000 - XXXX XXXX XXXX
    """
    bits_amount = 0
    base_value = 0
    if high_entropy and is_dll:
        base_value = 0x0000_7ff8_0000_0000  # 7FF8_0003_5ECB_0000
        bits_amount = 19
    elif high_entropy and not is_dll:
        bits_amount = 17
    elif not high_entropy and is_dll:
        bits_amount = 14
    else:
        bits_amount = 8

    return base_value + (random.getrandbits(bits_amount) << 16)


def section_perms_to_ms(section: lief.PE.Section) -> ms.AccessType:
    access = ms.AccessType.NONE
    if section.has_characteristic(lief.PE.Section.CHARACTERISTICS.MEM_READ):
        access |= ms.AccessType.R
    if section.has_characteristic(lief.PE.Section.CHARACTERISTICS.MEM_WRITE):
        access |= ms.AccessType.W
    if section.has_characteristic(lief.PE.Section.CHARACTERISTICS.MEM_EXECUTE):
        access |= ms.AccessType.X

    if access & ms.AccessType.WX == ms.AccessType.WX:
        log.info(f"WX Detected for {section.name}")

    return access


class PELoader(Plugin):
    """
    Loads PE files from disk.
    interact() can be used to map a PE file.
    """
    _INTERACT_TYPE = PELoaderInfo

    def __init__(self, *files: PELoaderInfo):
        super().__init__(*files)
        self._parsed: Dict[FileNameType, lief.PE.Binary] = {}
        self._loaded: Dict[FileNameType, LoadedPEInfo] = {}
        self._segment_plugin: Optional[Segment] = None
        self._stream_mapper: Optional[StreamMapper] = None

    def __getitem__(self, item: FileNameType) -> lief.PE.Binary:
        return self._parsed[item]

    def _prepare(self):
        self._segment_plugin = Plugin.require(Segment, self.emu)
        self._stream_mapper = Plugin.require(StreamMapper, self.emu)

    def _handle(self, obj: PELoaderInfo):
        if obj.file in self._loaded.keys():
            return

        log.info(f'Mapping PE {obj}')
        parsed = lief.PE.parse(obj.file)
        self._parsed[obj.file] = parsed

        # Pick base address
        base_address = self._pick_base(obj)
        self._loaded[obj.file] = LoadedPEInfo(obj, base_address)

        # Map main file
        self._map_headers(obj)

        # Create segments
        for section in parsed.sections:
            self._map_section(section, obj)

        # Import table

        # Apply relocations

    def is_base_ok(self, address: int, obj: lief.PE.Binary) -> bool:
        """
        Checks if the given address is unmapped
        :param address: Address to check
        :param obj: PE file to check
        :return: True if unmapped, False otherwise
        """
        if not self.ready:
            raise HSPluginInteractNotReadyError()

        if self.emu.mem.is_mapped(address, obj.virtual_size):
            return False

        # If megastone returned False, it might mean it couldn't find the segment
        # Example case: |(Start)|....|Seg Start|....|Seg End|....|(End)|

        for segment in self.emu.mem.segments:
            if segment.overlaps(ms.AddressRange(address, obj.virtual_size)):
                return False

        return True

    def _pick_base(self, obj: PELoaderInfo) -> int:
        if not self.ready:
            raise HSPluginInteractNotReadyError(f'For PE with {obj=}')

        parsed = self._parsed[obj.file]

        # Respect user's request first and foremost
        if obj.base is not None:
            if not parsed.is_pie:
                log.error(f'PE {obj} is not PIE, cannot respect user requested base {obj.base:#X}')
            elif self.is_base_ok(obj.base, parsed):
                return obj.base
            else:
                log.warning(f'PE {obj} cannot be mapped to {obj.base=:#X}')

        prefer_aslr = obj.prefer_aslr
        prefer_aslr &= parsed.optional_header.has(lief.PE.OptionalHeader.DLL_CHARACTERISTICS.DYNAMIC_BASE)

        if not prefer_aslr:
            # Attempt to respect base:
            if self.is_base_ok(parsed.imagebase, parsed):
                return parsed.imagebase
            else:
                log.warning(f'PE {obj} cannot be mapped at preferred base, falling back to ASLR')

        if parsed.is_pie:
            high_entropy = parsed.optional_header.has(lief.PE.OptionalHeader.DLL_CHARACTERISTICS.HIGH_ENTROPY_VA)
            is_dll = parsed.header.has_characteristic(lief.PE.Header.CHARACTERISTICS.DLL)
            base = calculate_aslr(high_entropy, is_dll) + parsed.imagebase

            retry = 5
            while (not self.is_base_ok(base, parsed)) and retry > 0:
                retry -= 1
                log.warning(f'Failed to choose ASLR for {obj}, {retry} attempts left')
                base = calculate_aslr(high_entropy, is_dll)

            if self.is_base_ok(base, parsed):
                log.debug(f'Generated ASLR {base:#X} for {obj}, {is_dll=} {high_entropy=}')
                return base

            log.error(f'ASLR attempt was futile, giving up')

        log.error(f'Cannot map PE {obj} - No PIE/ASLR Fail, cannot respect base nor user base.')
        raise HSPluginBadStateError(f'Unable to map PE {obj}')

    def _map_headers(self, pefile: PELoaderInfo):
        if not self.ready:
            raise HSPluginInteractNotReadyError(f'{pefile=}')

        self._stream_mapper.interact(
            StreamMapperInfo(
                stream=FileStream(pefile.file),
                segment=SegmentInfo(
                    f'PE.HEADER."{pefile.file}"',
                    self._loaded[pefile.file].base,
                    self._parsed[pefile.file].sizeof_headers,
                    perms=ms.AccessType.R
                )
            )
        )

    def _map_section(self, section: lief.PE.Section, pefile: PELoaderInfo):
        log.debug(f'Mapping section {section.name} of {pefile}')
        self._stream_mapper.interact(StreamMapperInfo(
            stream=RawStream(section.content.tobytes()),
            segment=SegmentInfo(
                f'PE.SECTION."{pefile.file}"."{section.name}"',
                self._loaded[pefile.file].base + section.virtual_address,
                section.virtual_size,
                section_perms_to_ms(section)
            )
        ))