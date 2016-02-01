import asyncio
import collections
import functools
from bottom.protocol import Protocol
from bottom.pack import pack_command


class Client:
    protocol = None

    def __init__(self, host, port, *, encoding="UTF-8", ssl=True, loop=None):
        self.host = host
        self.port = port
        self.ssl = ssl
        self.encoding = encoding

        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop

        self._handlers = collections.defaultdict(list)
        self._events = collections.defaultdict(
            lambda: asyncio.Event(loop=self.loop))

    @property
    def loop(self):
        """Do not change the event loop for a client"""
        return self._loop

    def send(self, command, **kwargs):
        """
        Send a message to the server.

        Examples
        --------
        client.send("nick", nick="weatherbot")
        client.send("privmsg", target="#python", message="Hello, World!")
        """
        packed_command = pack_command(command, **kwargs).strip()
        if not self.protocol:
            raise RuntimeError("Not connected")
        self.protocol.write(packed_command)

    async def connect(self):
        transport, protocol = await self.loop.create_connection(
            Protocol, host=self.host, port=self.port, ssl=self.ssl)
        if self.protocol:
            self.protocol.close()
        self.protocol = protocol
        protocol.client = self
        self.trigger("client_connect")

    async def disconnect(self):
        if self.protocol:
            self.protocol.close()

    def trigger(self, event, **kwargs):
        """Trigger all handlers for an event to (asynchronously) execute"""
        event = event.upper()
        for func in self._handlers[event]:
            self.loop.create_task(func(**kwargs))
        # This will unblock anyone that is awaiting on the next loop update,
        # while still ensuring the next `await client.wait(event)` doesn't
        # immediately fire.
        async_event = self._events[event]
        async_event.set()
        async_event.clear()

    async def wait(self, event):
        await self._events[event.upper()].wait()

    def on(self, event, func=None):
        """
        Decorate a function to be invoked when the given event occurs.

        The function may be a coroutine.  Your function should accept **kwargs
        in case an event is triggered with unexpected kwargs.

        Example
        -------
        import asyncio
        import bottom

        client = bottom.Client(...)
        @client.on("test")
        async def func(one, two, **kwargs):
            print(one)
            print(two)
            print(kwargs)

        events.trigger("test", **{"one": 1, "two": 2, "extra": "foo"})
        loop = asyncio.get_event_loop()
        # Run all queued events
        loop.stop()
        loop.run_forever()
        """
        if func is None:
            return functools.partial(self.on, event)
        wrapped = func
        if not asyncio.iscoroutinefunction(wrapped):
            wrapped = asyncio.coroutine(wrapped)
        self._handlers[event.upper()].append(wrapped)
        # Always return original
        return func

    def _connection_lost(self, protocol):
        # Ignore connection_lost for old connections
        if protocol is self.protocol:
            self.trigger("client_disconnect")
            self.protocol = None
