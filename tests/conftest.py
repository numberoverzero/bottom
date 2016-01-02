from bottom import Client
from bottom.connection import Connection
from bottom.event import EventsMixin
import pytest
import asyncio
import collections


@pytest.fixture
def loop():
    '''
    Keep things clean by using a new event loop
    '''
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
def schedule(loop):
    def _schedule(*coros):
        for coro in coros:
            loop.create_task(coro)
    return _schedule


@pytest.fixture
def connection(patch_connection, events, loop):
    print("connection")
    return Connection("host", "port", events, "UTF-8", True, loop=loop)


@pytest.fixture
def events(loop):
    ''' Return a no-op EventsMixin that tracks triggers '''
    return MockEvents(loop=loop)


@pytest.fixture
def reader():
    return MockStreamReader()


@pytest.fixture
def writer():
    return MockStreamWriter()


@pytest.fixture
def client(patch_connection, loop):
    '''
    Return a client with mocked out asyncio.

    Pulling in patch_connection here mocks out asyncio.open_connection,
    so that we can use reader, writer, run in tests.
    '''
    return Client("host", "port", loop=loop)


@pytest.fixture
def patch_connection(reader, writer, monkeypatch):
    '''
    Patch asyncio.open_connection to return a mock reader, writer.

    Returns the reader, writer pair for mocking
    '''
    @asyncio.coroutine
    def mock(*args, **kwargs):
        return reader, writer
    monkeypatch.setattr(asyncio, 'open_connection', mock)
    return reader, writer


@pytest.fixture
def watch():
    return Watcher()


class MockEvents(EventsMixin):
    def __init__(self, *, loop=None):
        self.triggered_events = collections.defaultdict(int)
        super().__init__(loop=loop)

    def trigger(self, event, **kwargs):
        self.triggered_events[event] += 1
        super().trigger(event, **kwargs)

    def triggered(self, event, n=1):
        '''
        Assert an event was triggered exactly n times (default exactly once)

        Pass n <= 0 to assert AT LEAST one call
        '''
        t = self.triggered_events[event]
        # Match exact expected call count
        if n > 0:
            return t == n
        # Assert at least one trigger
        return t > 0


class MockStreamReader():
    ''' Set up a reader that uses readline '''
    def __init__(self, encoding='UTF-8"'):
        self.lines = []
        self.read_lines = []
        self.encoding = encoding
        self.used = False

    async def readline(self):
        self.used = True
        try:
            line = self.lines.pop(0)
            self.read_lines.append(line)
            return line.encode(self.encoding)
        except IndexError:
            raise EOFError

    def push(self, line):
        ''' Push a string to be \n terminated and converted to bytes '''
        self.lines.append(line)

    def has_read(self, line):
        ''' return True if the given string was read '''
        return line in self.read_lines


class MockStreamWriter():
    ''' Set up a writer that captures written bytes as lines '''
    def __init__(self, encoding='UTF-8"'):
        self.written_lines = []
        self.encoding = encoding
        self._closed = False
        self.used = False

    def write(self, line):
        # store as bytes
        self.used = True
        self.written_lines.append(line)

    def close(self):
        self._closed = True

    @property
    def closed(self):
        return self._closed

    def has_written(self, line):
        ''' returns True if the given string was written '''
        # lines are stored as bytes - encode the string to test
        # and see if that's in written_lines
        return line.encode(self.encoding) in self.written_lines


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
