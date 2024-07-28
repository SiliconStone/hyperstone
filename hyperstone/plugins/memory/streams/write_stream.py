from hyperstone.plugins.memory.streams.stream import Stream
from hyperstone.plugins.base import Plugin
from hyperstone.util.logger import log


class StreamWriter(Plugin):
    """
    Generic stream writer plugin.
    This plugin allows writing streams to the hyperstone memory.
    """
    def __init__(self, *args: Stream):
        super().__init__(*args)

    def _handle(self, obj: Stream):
        """
        Write a stream to the emulator's memory.

        Args:
            obj: The stream to write.

        Raises:
            ValueError:
                If the stream has no base address.
                Similar to segments, a missing base address implies an upper layer failing to infer the base address.
        """
        if obj.base is None:
            raise ValueError(f'Cannot infer base address for {obj}')

        to_write = obj.raw(self.emu)
        self.emu.mem.write(obj.base, to_write)
        log.debug(f'Wrote {len(to_write):08X} bytes to {obj.base:08X}...')
