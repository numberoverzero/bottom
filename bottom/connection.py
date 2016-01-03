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

    async def connect(self):
        if self.connected:
            return
        self.reader, self.writer = await asyncio.open_connection(
            self.host, self.port, ssl=self.ssl, loop=self.loop)
        self._connected = True
        self.events.trigger("CLIENT_CONNECT", host=self.host, port=self.port)

    async def disconnect(self):
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

    async def run(self):
        await self.connect()
        while self.connected:
            msg = await self.read()
            if msg:
                try:
                    event, kwargs = unpack.unpack_command(msg)
                except ValueError:
                    print("PARSE ERROR {}".format(msg))
                else:
                    self.events.trigger(event, **kwargs)
            else:
                # Lost connection
                await self.disconnect()

    def send(self, msg):
        if self.writer:
            self.writer.write((msg.strip() + '\n').encode(self.encoding))

    async def read(self):
        if not self.reader:
            return ''
        try:
            msg = await self.reader.readline()
            return msg.decode(self.encoding, 'ignore').strip()
        except EOFError:
            return ''
