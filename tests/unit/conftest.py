from bottom.client import Client
from bottom.protocol import Protocol
import pytest
import asyncio
import collections
NOT_CORO = "Can't schedule non-coroutine"


@pytest.fixture
def watch():
    return Watcher()


@pytest.fixture
def loop(transport, protocol):
    """
    Keep things clean by using a new event loop
    """
    loop = asyncio.new_event_loop()
    loop.set_debug(True)

    async def create_connection(protocol_factory, *args, **kwargs):
        protocol.connection_made(transport)
        return transport, protocol
    loop.create_connection = create_connection

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
def schedule(loop, flush):
    def _schedule(*coros, immediate=True):
        for coro in coros:
            assert asyncio.iscoroutine(coro), NOT_CORO
            loop.create_task(coro)
        if immediate:
            flush()
    return _schedule


@pytest.fixture
def protocol():
    return Protocol()


@pytest.fixture
def transport(protocol):
    class Transport:
        def __init__(self):
            self.written = []
            self.closed = False

        def write(self, data):
            self.written.append(data)

        def close(self):
            self.closed = True
            protocol.connection_lost(exc=None)
    return Transport()


@pytest.fixture
def client(loop):
    """
    Return a client that tracks triggers and connects to reader/writer.
    """
    return TrackingClient("host", "port", loop=loop)


class TrackingClient(Client):
    def __init__(self, *args, **kwargs):
        self.triggers = collections.defaultdict(int)
        super().__init__(*args, **kwargs)

    def trigger(self, event, **kwargs):
        event = event.upper()
        self.triggers[event] += 1
        super().trigger(event, **kwargs)


class Watcher():
    """Exposes `call` function, `calls` attribute, and `called` property.
    Useful for lambdas that can't += a variable"""
    def __init__(self):
        self.calls = 0

    def call(self):
        self.calls += 1

    @property
    def called(self):
        return self.calls > 0
