from __future__ import annotations

import asyncio
import collections
import ssl as ssl_module
import typing as t

import bottom
import pytest
import pytest_asyncio


@pytest.fixture
def host() -> str:
    return "localhost"


@pytest.fixture
def port() -> int:
    return 8888


@pytest.fixture
def encoding() -> str:
    return "utf-8"


@pytest.fixture
def ssl() -> ssl_module.SSLContext | bool | None:
    # TODO: make a working context
    # return _ssl.create_default_context()
    return None


@pytest_asyncio.fixture
async def client(host, port, ssl, encoding) -> t.AsyncGenerator[bottom.Client]:
    class TrackingClient(bottom.Client):
        def __init__(self, *args, **kwargs):
            self.triggers = collections.defaultdict(int)
            super().__init__(*args, **kwargs)

        def trigger(self, event, **kwargs) -> asyncio.Task:
            event = event.strip().upper()
            self.triggers[event] += 1
            return super().trigger(event, **kwargs)

    client = TrackingClient(host=host, port=port, ssl=ssl, encoding=encoding)
    yield client
    await client.disconnect()


class ServerProtocol(asyncio.Protocol):
    delim_lax = b"\n"
    delim_strict = b"\r\n"
    buffer = b""

    def __init__(self, server: Server, encoding: str) -> None:
        self.server = server
        self.encoding = encoding

    def connection_made(self, transport: asyncio.WriteTransport):  # type: ignore[override]
        self.transport = transport

    def data_received(self, data):
        self.buffer += data
        # Assume a strict server that only recognizes the spec's line ending
        *lines, self.buffer = self.buffer.split(self.delim_strict)
        for line in lines:
            incoming = line.decode(self.encoding, "ignore").strip()
            self.server.handle(incoming)

    def write(self, outgoing):
        outgoing = outgoing.strip()
        # Assume a non-compliant server that doesn't write the full line ending
        data = outgoing.encode(self.encoding) + self.delim_lax
        self.transport.write(data)

    def close(self):
        self.transport.close()


class Server:
    protocol: ServerProtocol

    def __init__(self, host: str, port: int, ssl: ssl_module.SSLContext | bool | None, encoding: str):
        self.host = host
        self.port = port
        self.ssl = ssl
        self.encoding = encoding
        self.expected = {}
        self.received = []
        self.sent = []

    async def start(self):
        loop = asyncio.get_running_loop()

        def protocol_factory():
            protocol = ServerProtocol(self, self.encoding)
            self.protocol = protocol
            return protocol

        self._server = await loop.create_server(protocol_factory, host=self.host, port=self.port, ssl=self.ssl)

    async def close(self):
        self._server.close()
        self.protocol.close()
        await self._server.wait_closed()

    def expect(self, incoming, response=None):
        self.expected[incoming] = response

    def handle(self, incoming):
        self.received.append(incoming)
        outgoing = self.expected[incoming]
        self.sent.append(outgoing)
        self.protocol.write(outgoing)

    def write(self, outgoing):
        self.sent.append(outgoing)
        self.protocol.write(outgoing)


@pytest_asyncio.fixture
async def server(client: bottom.Client) -> t.AsyncGenerator[Server]:
    server = Server(
        host=client.host,
        port=client.port,
        ssl=client.ssl,
        encoding=client.encoding,
    )
    yield server
    await server.close()
