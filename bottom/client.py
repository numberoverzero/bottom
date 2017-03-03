import asyncio
import collections
import functools
from typing import Any, Callable, DefaultDict, List, Optional  # noqa
from bottom.protocol import Protocol
from bottom.pack import pack_command


class Client:
    protocol = None  # type: Optional[Protocol]

    _handlers = None  # type: DefaultDict[str, List[Callable]]
    _events = None  # type: DefaultDict[str, asyncio.Event]

    def __init__(self, host: str, port: int, *,
                 encoding: str = "UTF-8", ssl: bool = True,
                 loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
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
    def loop(self) -> asyncio.AbstractEventLoop:
        """Do not change the event loop for a client"""
        return self._loop

    def send(self, command: str, **kwargs: Any) -> None:
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

    async def connect(self) -> None:
        def protocol_factory() -> Protocol:
            return Protocol(client=self)

        # See https://github.com/python/typeshed/issues/953
        _, protocol = await self.loop.create_connection(  # type: ignore
            protocol_factory, host=self.host, port=self.port, ssl=self.ssl)
        if self.protocol:
            self.protocol.close()
        self.protocol = protocol
        # TODO: Delete the following code line. It is currently kept in order
        # to not break the current existing codebase. Removing it requires a
        # heavy change in the test codebase.
        protocol.client = self
        self.trigger("client_connect")

    async def disconnect(self) -> None:
        if self.protocol:
            self.protocol.close()

    def trigger(self, event: str, **kwargs: Any) -> None:
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

    async def wait(self, event: str) -> None:
        await self._events[event.upper()].wait()

    def on(self, event: str, func: Optional[Callable] = None) -> Callable:
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
            return functools.partial(self.on, event)  # type: ignore
        wrapped = func
        if not asyncio.iscoroutinefunction(wrapped):
            wrapped = asyncio.coroutine(wrapped)
        self._handlers[event.upper()].append(wrapped)
        # Always return original
        return func

    def _connection_lost(self, protocol: asyncio.Protocol) -> None:
        # Ignore connection_lost for old connections
        if protocol is self.protocol:
            self.trigger("client_disconnect")
            self.protocol = None
