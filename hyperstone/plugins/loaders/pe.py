from dataclasses import dataclass
from itertools import chain
from typing import Optional, Dict, List, Callable, Any#, Self
from typing_extensions import Self

import random
import lief.PE
import megastone as ms

from hyperstone.plugins.memory.mappers.map_stream import StreamMapper, StreamMapperInfo
from hyperstone.plugins.memory.access_enforce import EnforceMemory, EnforceMemoryInfo
from hyperstone.plugins.memory.mappers.map_segment import Segment, SegmentInfo
from hyperstone.plugins.memory.streams.write_file import FileStream
from hyperstone.plugins.memory.streams.write_raw import RawStream

from hyperstone.plugins.hooks.base import Hook, HookInfo, ActiveHook
from hyperstone.plugins.base import Plugin
from hyperstone.emulator import HyperEmu
from hyperstone.exceptions import HSPluginInteractNotReadyError, HSPluginBadStateError
from hyperstone.util.logger import log


FileNameType = str


@dataclass(frozen=True)
class PELoaderInfo:
    """
    Represents a PE file that we want to map

    Vars:
        file: The path to a file we want to load
        base: An optional base address for the PE file
        prefer_aslr: Should we try to map with ASLR enabled?
        map_sections_rwx: Should map the header as RWX?
    """
    file: FileNameType
    base: Optional[int] = None
    prefer_aslr: bool = False
    map_header_rwx: bool = False


@dataclass(frozen=True)
class MappedPE:
    info: PELoaderInfo
    base: int
    pe: lief.PE.Binary

    @property
    def entrypoint(self):
        return self.base + self.pe.optional_header.addressof_entrypoint

    def function(self, name: str) -> int:
        for func in chain(self.pe.exported_functions, self.pe.functions):
            if func.name == name:
                return self.base + func.address

        log.error(f"Function {name} not found")


def calculate_aslr(high_entropy: bool, is_dll: bool) -> int:
    """
    Suggest an ASLR'd base

    Vars:
        high_entropy: Related to the Char in OptionalHeader, means we support >4GB 64bit ASLR
        is_dll: DLLs have higher ASLR range

    Returns:
        A proposed base (with ASLR)

    Notes:
        ASLR in windows -
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
    base_value = 0
    if high_entropy and is_dll:
        base_value = 0x0000_7ff0_0000_0000  # 7FF8_0003_5ECB_0000
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
    _IAT_HOOK_SEP = '@'

    def __init__(self, *files: PELoaderInfo):
        super().__init__(*files)
        self._loaded: Dict[FileNameType, MappedPE] = {}
        self._phantom_hooks: Dict[str, Dict[str, int]] = {}
        self._iat_hooks: Dict[str, Callable[[HyperEmu, dict], Any]] = {}
        self._segment_plugin: Optional[Segment] = None
        self._stream_mapper: Optional[StreamMapper] = None
        self._enforce_plugin: Optional[EnforceMemory] = None
        self._hook_plugin: Optional[Hook] = None

    def __getitem__(self, item: FileNameType) -> MappedPE:
        return self._loaded[item]

    def missing_iat(self, name: str, callback: Callable[[HyperEmu, dict], Any]) -> Self:
        """
        Put a hook on a IAT entry that wasn't loaded
        Args:
            name: The name of the IAT entry, for example (KERNEL32.DLL!LoadLibraryA)
            callback: The callback function to use

        Returns:
            self, for chaining inside classes / Settings
        """
        self._iat_hooks[name] = callback
        return self

    def _prepare(self):
        self._segment_plugin = Plugin.require(Segment, self.emu)
        self._stream_mapper = Plugin.require(StreamMapper, self.emu)
        for plugin in Plugin.get_all_loaded(Hook, self.emu):
            self._hook_plugin = plugin
            log.info('Found Hook plugin, will attempt to hook every missing IAT entry')
            break
        for plugin in Plugin.get_all_loaded(EnforceMemory, self.emu):
            self._enforce_plugin = plugin
            log.info("Found EnforceMemory plugin, promoting StreamMapper and mapping all Segments as RWX to override "
                     "megastone page protection system.")

            # Need stream_mapper to act instantly in case of EnforceMemory
            # That way, we can use EnforceMemory with a mapped ms.Segment
            self._stream_mapper.prepare(self.emu)
            break

    def _handle(self, obj: PELoaderInfo):
        if obj.file in self._loaded.keys():
            return

        log.info(f'Mapping PE {obj}')
        parsed = lief.PE.parse(obj.file)

        # Pick base address
        base_address = self._pick_base(obj, parsed)
        mapped = MappedPE(obj, base_address, parsed)
        self._loaded[obj.file] = mapped

        # Map main file
        self._map_headers(mapped)

        # Create segments
        for section in parsed.sections:
            self._map_section(section, mapped)

        # Import table
        self._handle_iats(mapped)

        # Apply relocations
        self._handle_reloc(mapped)

    def is_base_ok(self, address: int, obj_virtual_size: int) -> bool:
        """
        Checks if the given address is unmapped

        Vars:
            address: Address to check
            obj: PE file to check

        Returns:
            True if unmapped, False otherwise
        """
        if not self.ready:
            raise HSPluginInteractNotReadyError()

        if address == 0:
            return False

        if self.emu.mem.is_mapped(address, obj_virtual_size):
            return False

        # If megastone returned False, it might mean it couldn't find the segment
        # Example case: |(Start)|....|Seg Start|....|Seg End|....|(End)|

        for segment in self.emu.mem.segments:
            if segment.overlaps(ms.AddressRange(address, obj_virtual_size)):
                return False

        return True

    def _pick_base(self, obj: PELoaderInfo, parsed: lief.PE.Binary) -> int:
        if not self.ready:
            raise HSPluginInteractNotReadyError(f'For PE with {obj=}')

        # Respect user's request first and foremost
        if obj.base is not None:
            if not parsed.is_pie:
                log.error(f'PE {obj} is not PIE, cannot respect user requested base {obj.base:#X}')
            elif self.is_base_ok(obj.base, parsed.virtual_size):
                return obj.base
            else:
                log.warning(f'PE {obj} cannot be mapped to {obj.base=:#X}')

        prefer_aslr = obj.prefer_aslr
        prefer_aslr &= parsed.optional_header.has(lief.PE.OptionalHeader.DLL_CHARACTERISTICS.DYNAMIC_BASE)

        if not prefer_aslr:
            # Attempt to respect base:
            if self.is_base_ok(parsed.imagebase, parsed.virtual_size):
                return parsed.imagebase
            else:
                log.warning(f'PE {obj} cannot be mapped at preferred base, falling back to ASLR')

        if parsed.is_pie:
            high_entropy = parsed.optional_header.has(lief.PE.OptionalHeader.DLL_CHARACTERISTICS.HIGH_ENTROPY_VA)
            is_dll = parsed.header.has_characteristic(lief.PE.Header.CHARACTERISTICS.DLL)
            base = calculate_aslr(high_entropy, is_dll) + parsed.imagebase

            retry = 5
            while (not self.is_base_ok(base, parsed.virtual_size)) and retry > 0:
                retry -= 1
                log.warning(f'Failed to choose ASLR for {obj}, {retry} attempts left')
                base = calculate_aslr(high_entropy, is_dll)

            if self.is_base_ok(base, parsed.virtual_size):
                log.debug(f'Generated ASLR {base:#X} for {obj}, {is_dll=} {high_entropy=}')
                return base

            log.error(f'ASLR attempt was futile, giving up')

        log.error(f'Cannot map PE {obj} - No PIE/ASLR Fail, cannot respect base nor user base.')
        raise HSPluginBadStateError(f'Unable to map PE {obj}')

    def _map_headers(self, mapped: MappedPE):
        if not self.ready:
            raise HSPluginInteractNotReadyError(f'{mapped.info=}')

        pefile = mapped.info
        perm = ms.AccessType.RWX if pefile.map_header_rwx else ms.AccessType.R

        self._stream_mapper.interact(
            StreamMapperInfo(
                stream=FileStream(pefile.file),
                segment=SegmentInfo(
                    f'PE.HEADER."{pefile.file}"',
                    mapped.base,
                    mapped.pe.sizeof_headers,
                    perms=perm
                )
            )
        )

    def _map_section(self, section: lief.PE.Section, mapped: MappedPE):
        if not self.ready:
            raise HSPluginInteractNotReadyError(f'{mapped.info=}')

        # Implement our Segments in EnforceMemory if exists, otherwise use Megastone's default protection engine
        # Sometimes, Segments are too close to one another, when that happens megastone cannot enforce per-page
        # permissions
        permission = section_perms_to_ms(section)
        enforce_perm = permission

        if self._enforce_plugin is not None:
            permission = ms.AccessType.RWX

        pefile = mapped.info
        segment_name = f'PE.SECTION."{pefile.file}"."{section.name}"'
        log.debug(f'Mapping section {section.name} of {pefile}')
        self._stream_mapper.interact(StreamMapperInfo(
            stream=RawStream(section.content.tobytes()),
            segment=SegmentInfo(
                segment_name,
                mapped.base + section.virtual_address,
                section.virtual_size,
                permission
            )
        ))

        if self._enforce_plugin is not None:
            # Force our mapper to work now in order to be able to pull the ms.Segment object
            self._stream_mapper.prepare(self.emu)
            self._enforce_plugin.interact(
                EnforceMemoryInfo(
                    self._segment_plugin.mapped(segment_name),
                    enforce_perm,
                )
            )

    def _handle_iats(self, mapped: MappedPE):
        if not self.ready:
            raise HSPluginInteractNotReadyError(f'{mapped.info=}')

        parsed = mapped.pe
        for dependency in parsed.imports:
            dependency: lief.PE.Import

            loaded_item = None

            for loaded in self._loaded.copy():
                if dependency.name not in loaded:
                    for item in self._interact_queue:
                        item: PELoaderInfo
                        if dependency.name in item.file:
                            self._handle(item)  # Load our dependency real quick
                            loaded_item = self._loaded[item.file]
                            break
                else:
                    loaded_item = self._loaded[loaded]
                    break
            else:
                if loaded_item is None:
                    log.warning(f'IAT dependency {dependency.name} for {mapped.info} not found.')
                    self._handle_missing_iat(dependency, mapped)
                    continue

            self._load_iat(mapped, dependency, loaded_item)

    def _load_iat(self, mapped: MappedPE, dependency: lief.PE.Import, lib: MappedPE):
        if not self.ready:
            raise HSPluginInteractNotReadyError(f'{mapped.info=}')

        my_base = mapped.base
        exports = {}

        parsed = self._loaded[lib.info.file].pe
        for export in parsed.get_export().entries:
            export: lief.PE.ExportEntry
            exports[export.name] = export

        for entry in dependency.entries:
            entry: lief.PE.ImportEntry
            if entry.name not in exports:
                log.error(f'IAT dependency {dependency.name} missing symbol {entry.name} for {mapped.info}.')
                continue

            export = exports[entry.name]
            log.debug(f'Loading IAT {dependency.name}!{export.name} for {mapped.info}')
            self.emu.mem.write_word(my_base + entry.iat_address, lib.base + export.function_rva)

    def _handle_missing_iat(self, dependency: lief.PE.Import, mapped: MappedPE):
        if dependency.name not in self._phantom_hooks:
            self._phantom_hooks[dependency.name] = {}

        base = self.map_fake_dll(dependency, mapped)

        for entry in dependency.entries:
            entry: lief.PE.ImportEntry
            if entry in self._phantom_hooks[dependency.name]:
                log.warning(f'IAT dependency {dependency.name}!{entry.name} mapped at '
                            f'{self._phantom_hooks[dependency.name][entry.name]:#X}')
                continue

            my_base = mapped.base

            self._phantom_hooks[dependency.name][entry.name] = base
            self.emu.mem.write_word(my_base + entry.iat_address, base)

            if self._hook_plugin is not None:
                self._hook_plugin.interact(HookInfo(
                    f'IAT{self._IAT_HOOK_SEP}{dependency.name}!{entry.name}',
                    base,
                    None,
                    self._phantom_hook_callback,
                ))
            else:
                log.error('No Hook plugin was loaded in the current project. '
                          'Please load one if you want to use IAT hooks feature')
            base += self.emu.arch.word_size

    def map_fake_dll(self, dependency: lief.PE.Import, mapped: MappedPE) -> int:
        parsed = mapped.pe
        retry = 5
        base = 0
        is64 = parsed.optional_header.has(lief.PE.OptionalHeader.DLL_CHARACTERISTICS.HIGH_ENTROPY_VA)
        while (not self.is_base_ok(base, parsed.virtual_size)) and retry > 0:
            retry -= 1
            base = calculate_aslr(is64, True)

        self._segment_plugin.interact(
            SegmentInfo(f'IAT PLT for {dependency.name}', base,
                        len(dependency.entries) * self.emu.arch.word_size)
        )

        return base

    def _handle_reloc(self, mapped: MappedPE):
        parsed = mapped.pe
        base = mapped.base
        for reloc in parsed.relocations:
            reloc: lief.PE.Relocation
            for entry in reloc.entries:
                entry: lief.PE.RelocationEntry

                if entry.type == lief.PE.RelocationEntry.BASE_TYPES.ABS:
                    continue

                reloc_offset = base + reloc.virtual_address + entry.position
                old_val = self.emu.mem.read_word(reloc_offset)
                self.emu.mem.write_word(reloc_offset, old_val - parsed.imagebase + base)

    def _phantom_hook_callback(self, emu: HyperEmu, ctx: Dict[str, Any]):

        hook: ActiveHook = ctx[self._hook_plugin.CTX_HOOK]
        hook_fn = hook.type.name.split(self._IAT_HOOK_SEP)[-1]

        if hook_fn in self._iat_hooks and self._iat_hooks[hook_fn] is not None:
            self._iat_hooks[hook_fn](emu, ctx)

