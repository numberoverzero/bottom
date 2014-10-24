from bottom.event import EventsMixin
import pytest
import asyncio
import collections


@pytest.fixture
def run():
    ''' Run a coro until it completes '''
    def run_in_loop(coro):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(coro)
    return run_in_loop


@pytest.fixture
def events():
    ''' Return a no-op EventsMixin that tracks triggers '''
    return MockEvents()


@pytest.fixture
def reader():
    return MockStreamReader()


@pytest.fixture
def writer():
    return MockStreamWriter()


@pytest.fixture
def patch_connection(reader, writer, monkeypatch):
    '''
    Patch asyncio.open_connection to return a mock reader, writer.

    Returns the reader, writer pair for mocking
    '''
    mock = mock_connection(reader, writer)
    monkeypatch.setattr(asyncio, 'open_connection', mock)
    return reader, writer


class MockEvents(EventsMixin):
    def __init__(self):
        self.triggered_events = collections.defaultdict(int)
        super().__init__(None)

    @asyncio.coroutine
    def trigger(self, event, **kwargs):
        self.triggered_events[event] += 1

    def triggers(self, event):
        ''' Number of times an event was triggered '''
        return self.triggered_events[event]


class MockStreamReader():
    ''' Set up a reader that uses readline '''
    def __init__(self, encoding='UTF-8"'):
        self.lines = []
        self.read_lines = []
        self.encoding = encoding

    @asyncio.coroutine
    def readline(self):
        try:
            line = self.lines.pop(0)
            self.read_lines.append(line)
            yield (line + '\n').encode(self.encoding)
        except IndexError:
            raise EOFError

    def push(self, line):
        ''' Push a string to be \n terminated and converted to bytes '''
        self.lines.append(line)

    @property
    def used(self):
        ''' True if at least one line was read '''
        return bool(self.read_lines)

    def has_read(self, line):
        ''' return True if the given string was read '''
        return line in self.read_lines


class MockStreamWriter():
    ''' Set up a writer that captures written bytes as lines '''
    def __init__(self, encoding='UTF-8"'):
        self.written_lines = []
        self.encoding = encoding
        self._closed = False

    def write(self, line):
        # store as bytes
        self.written_lines.append(line)

    def close(self):
        self._closed = True

    @property
    def closed(self):
        return self._closed

    @property
    def used(self):
        ''' True if at least one line was written '''
        return bool(self.written_lines)

    def has_written(self, line):
        ''' returns True if the given string was written '''
        # lines are stored as bytes - encode the string to test
        # and see if that's in written_lines
        return line.encode(self.encoding) in self.written_lines


def mock_connection(reader, writer, **expected):
    '''
    returns a function to replace `asyncio.open_connection`

    the returned function validates any expected kwargs (optional) and
    passed back the (reader, writer) pair.
    '''
    missing = object()

    @asyncio.coroutine
    def mock_open_connection(*args, **kwargs):
        for key, value in expected.items():
            assert kwargs.get(key, missing) == value
        return reader, writer
    return mock_open_connection
