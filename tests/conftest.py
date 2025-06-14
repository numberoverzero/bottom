from __future__ import annotations

import asyncio
import collections
import os
import ssl as ssl_module
import sys
import typing as t

import bottom
import bottom.core
import pytest
import pytest_asyncio

# allow imports using "from tests.package import foo"
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


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
    protocol: ServerProtocol | None = None

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

        self._server = await loop.create_server(
            protocol_factory,
            host=self.host,
            port=self.port,
            ssl=self.ssl,
            # start_serving so that we can await start() immediately
            start_serving=True,
        )

    async def close(self):
        self._server.close()
        if self.protocol:
            self.protocol.close()
        await self._server.wait_closed()

    def expect(self, incoming, response=None):
        self.expected[incoming] = response

    def handle(self, incoming):
        self.received.append(incoming)
        # respond if we have one
        if incoming in self.expected:
            outgoing = self.expected[incoming]
            self.sent.append(outgoing)
            assert self.protocol
            self.protocol.write(outgoing)

    def write(self, outgoing):
        self.sent.append(outgoing)
        assert self.protocol
        self.protocol.write(outgoing)


@pytest.fixture
def host() -> str:
    return "localhost"


@pytest.fixture
def encoding() -> str:
    return "utf-8"


@pytest.fixture
def ssl() -> ssl_module.SSLContext | bool | None:
    # TODO: make a working context
    # return _ssl.create_default_context()
    return None


@pytest_asyncio.fixture
async def server(host, ssl, encoding) -> t.AsyncGenerator[Server]:
    server = Server(
        host=host,
        port=0,  # find a free port; other fixtures will get port off from the server
        ssl=ssl,
        encoding=encoding,
    )
    await server.start()
    try:
        yield server
    finally:
        await server.close()


@pytest.fixture
def port(server: Server) -> int:
    return server._server.sockets[0].getsockname()[1]


@pytest.fixture
def server_protocol(server: Server) -> ServerProtocol:
    assert server.protocol is not None
    return server.protocol  # ty: ignore  # https://github.com/astral-sh/ty/issues/164


@pytest_asyncio.fixture
async def client(port, host, ssl, encoding) -> t.AsyncGenerator[bottom.Client]:
    class TrackingClient(bottom.Client):
        def __init__(self, *args, **kwargs):
            self.triggers = collections.defaultdict(int)
            super().__init__(*args, **kwargs)

        def trigger(self, event, **kwargs) -> asyncio.Task:
            event = event.strip().upper()
            self.triggers[event] += 1
            return super().trigger(event, **kwargs)

    client = TrackingClient(host=host, port=port, ssl=ssl, encoding=encoding)
    try:
        yield client
    finally:
        await client.disconnect()


@pytest_asyncio.fixture
async def client_protocol(client: bottom.Client) -> bottom.core.Protocol | None:
    await client.connect()
    return client._protocol


@pytest.fixture
def captured_messages(client: bottom.Client) -> t.Iterable[list[bytes]]:
    """injects a message handler that captures all incoming messages"""
    captured: list[bytes] = []

    async def capture_message(next_handler, client, message):
        captured.append(message)
        await next_handler(client, message)

    client.message_handlers.insert(0, capture_message)
    try:
        yield captured
    finally:
        client.message_handlers.remove(capture_message)
