import asyncio
import collections
import functools
from bottom.protocol import Protocol
from bottom.pack import pack_command


class Client:
    def __init__(self, host, port, *, encoding="UTF-8", ssl=True, loop=None):
        self.host = host
        self.port = port
        self.encoding = encoding
        self.protocol = None
        self.ssl = ssl
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop
        self._handlers = collections.defaultdict(list)

    def send(self, command, **kwargs):
        """
        Send a message to the server.

        Examples
        --------
        client.send("nick", nick="weatherbot")
        client.send("privmsg", target="#python", message="Hello, World!")
        """
        packed_command = pack_command(command, **kwargs)
        self.connection.send(packed_command)

    def connect(self):
        if self.connected:
            return
        coro = self.loop.create_connection(
            Protocol.factory(self),
            host=self.host, port=self.port, ssl=self.ssl)
        self.loop.create_task(coro)

    def disconnect(self):
        if not self.connected:
            return
        self.protocol.close()

    @property
    def connected(self):
        return (self.protocol is not None) and self.protocol.connected

    def trigger(self, event, **kwargs):
        """Trigger all handlers for an event to (asynchronously) execute"""
        for func in self._handlers[event.upper()]:
            self.loop.create_task(func(**kwargs))

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
