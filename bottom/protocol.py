import asyncio
import logging
from bottom.unpack import unpack_command
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from bottom.client import Client  # noqa

# Always write the full \r\n per spec, but accept \n when reading
DELIM = b"\r\n"
DELIM_COMPAT = b"\n"
log = logging.getLogger('bottom')


class Protocol(asyncio.Protocol):
    client = None  # type: Client
    closed = False  # type: bool
    transport = None  # type: asyncio.Transport
    buffer = b""  # type: bytes

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        assert isinstance(transport, asyncio.Transport)
        self.transport = transport

    def connection_lost(self, exc: Optional[Exception]) -> None:
        if not self.closed:
            self.closed = True
            self.close()
            self.client._connection_lost(self)

    def data_received(self, data: bytes) -> None:
        self.buffer += data
        # All but the last result of split should be pushed into the
        # client.  The last will be b"" if the buffer ends on b"\n"
        *lines, self.buffer = self.buffer.split(DELIM_COMPAT)
        for line in lines:
            message = line.decode(self.client.encoding, "ignore").strip()
            try:
                event, kwargs = unpack_command(message)
                self.client.trigger(event, **kwargs)
            except ValueError:
                log.debug("Failed to parse line >>> {}".format(message))

    def write(self, message: str) -> None:
        message = message.strip()
        data = message.encode(self.client.encoding) + DELIM
        self.transport.write(data)

    def close(self) -> None:
        if not self.closed:
            try:
                self.transport.close()
            finally:
                self.closed = True
