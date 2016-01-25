import asyncio
import collections
import pytest
# import ssl as _ssl

import bottom


@pytest.fixture
def host():
    return 'localhost'


@pytest.fixture
def port():
    return 8888


@pytest.fixture
def ssl():
    # TODO: make a working context
    # return _ssl.create_default_context()
    return None


@pytest.fixture
def loop():
    loop = asyncio.new_event_loop()
    loop.set_debug(True)
    return loop


@pytest.fixture
def flush(loop):
    """Run loop once, to execute any pending tasks"""
    async def sentinel():
        pass

    def _flush():
        loop.run_until_complete(sentinel())
    return _flush


@pytest.fixture
def waiter(loop):
    """Return a pair of functions for marking and waiting on an async event,
    in a synchronous call.

    Example
    =======
    def test_ping(client, server, connect, waiter):
        mark, wait = waiter()

        @client.on("ping")
        def handle(**kw):
            client.send("pong")
            mark()
        connect()
        server.send("PING :msg")
        wait()
        assert client.triggers["PING"] == 1
    """
    def _waiter():
        event = asyncio.Event(loop=loop)
        return (
            lambda: event.set(),
            lambda: loop.run_until_complete(event.wait()))
    return _waiter


@pytest.fixture
def client(loop, host, port, ssl):
    class TrackingClient(bottom.Client):
        def __init__(self, *args, **kwargs):
            self.triggers = collections.defaultdict(int)
            super().__init__(*args, **kwargs)

        def trigger(self, event, **kwargs):
            event = event.upper()
            self.triggers[event] += 1
            super().trigger(event, **kwargs)

    return TrackingClient(host=host, port=port, loop=loop, ssl=ssl)


@pytest.fixture
def protocol(client, loop):
    """Server side protocol"""
    class Protocol(asyncio.Protocol):
        delim = b"\n"
        delim_compat = b"\r\n"
        buffer = b""

        @classmethod
        def factory(cls, server):
            return lambda: cls(server)

        def __init__(self, server):
            self.server = server
            server.protocol = self
            super().__init__()

        def connection_made(self, transport):
            self.transport = transport

        def data_received(self, data):
            self.buffer += data
            # Assume a strict server that only recognizes the spec's \r\n
            *lines, self.buffer = self.buffer.split(b"\r\n")
            for line in lines:
                incoming = line.decode(client.encoding, "ignore").strip()
                self.server.handle(incoming)

        def write(self, outgoing):
            outgoing = outgoing.strip()
            # Assume a non-compliant server that only writes \n
            data = outgoing.encode(client.encoding) + b"\n"
            self.transport.write(data)

        def close(self):
            self.transport.close()

    return Protocol


@pytest.yield_fixture
def server(protocol, loop, host, port, ssl):
    class Server:
        def __init__(self):
            self.expected = {}
            self.received = []
            self.sent = []

        async def start(self):
            self._server = await loop.create_server(
                protocol.factory(self), host, port, ssl=ssl)

        def close(self):
            self._server.close()
            loop.run_until_complete(self._server.wait_closed())

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
    server = Server()
    yield server
    server.close()


@pytest.fixture
def connect(server, client, loop):
    def _connect():
        loop.run_until_complete(server.start())
        loop.run_until_complete(client.connect())
    return _connect
