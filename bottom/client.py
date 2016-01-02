import asyncio
import functools
from bottom.connection import Connection
from bottom.pack import pack_command


class Client:
    def __init__(self, host, port, *, encoding="UTF-8", ssl=True, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop
        self._handlers = {}
        self.connection = Connection(host, port, self, ssl=ssl,
                                     encoding=encoding, loop=loop)

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

    async def connect(self):
        await self.connection.connect()

    async def disconnect(self):
        await self.connection.disconnect()

    @property
    def connected(self):
        return self.connection.connected

    async def run(self):
        """Run the client until it disconnects"""
        await self.connection.run()

    def _add_event(self, event, func):
        """
        Validate the func's signature, then partial_bind the function to speed
        up argument injection.
        """
        if not asyncio.iscoroutinefunction(func):
            func = asyncio.coroutine(func)
        if event not in self._handlers:
            self._handlers[event] = list()
        self._handlers[event].append(func)
        # Returned func is not necessarily the original
        return func

    def trigger(self, event, **kwargs):
        """Trigger all handlers for an event to (asynchronously) execute"""
        for func in self._handlers.get(event.upper(), []):
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
        self._add_event(event.upper(), func)
        return func
