import asyncio
from . import unpack


class Connection(object):
    def __init__(self, host, port, events, encoding, ssl, *, loop):
        self.events = events
        self._connected = False
        self.host, self.port = host, port
        self.reader, self.writer = None, None
        self.encoding = encoding
        self.ssl = ssl
        self.loop = loop

    @asyncio.coroutine
    def connect(self):
        if self.connected:
            return
        self.reader, self.writer = yield from asyncio.open_connection(
            self.host, self.port, ssl=self.ssl, loop=self.loop)
        self._connected = True
        self.events.trigger("CLIENT_CONNECT", host=self.host, port=self.port)

    @asyncio.coroutine
    def disconnect(self):
        if not self.connected:
            return
        self.writer.close()
        self.writer = None
        self.reader = None
        self._connected = False
        self.events.trigger(
            "CLIENT_DISCONNECT", host=self.host, port=self.port)

    @property
    def connected(self):
        return self._connected

    @asyncio.coroutine
    def run(self):
        yield from self.connect()
        while self.connected:
            msg = yield from self.read()
            if msg:
                try:
                    event, kwargs = unpack.unpack_command(msg)
                except ValueError:
                    print("PARSE ERROR {}".format(msg))
                else:
                    self.events.trigger(event, **kwargs)
            else:
                # Lost connection
                yield from self.disconnect()

    def send(self, msg):
        if self.writer:
            self.writer.write((msg.strip() + '\n').encode(self.encoding))

    @asyncio.coroutine
    def read(self):
        if not self.reader:
            return ''
        try:
            msg = yield from self.reader.readline()
            return msg.decode(self.encoding, 'ignore').strip()
        except EOFError:
            return ''
