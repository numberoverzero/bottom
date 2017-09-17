import asyncio
import collections
import functools
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple  # noqa
from bottom.protocol import Protocol
from bottom.pack import pack_command
from bottom.unpack import unpack_command


async def process(handlers: List[Callable], message: str) -> None:
    if not handlers:
        return

    # noinspection PyShadowingNames
    async def noop_handler(next_handler: Callable, message: str) -> None:
        assert not handler_queue

    handler_queue = collections.deque([*handlers, noop_handler])

    # noinspection PyShadowingNames
    async def next_handler(message: str) -> None:
        handler = handler_queue.popleft()  # type: Any
        assert asyncio.iscoroutinefunction(handler)
        await handler(next_handler, message)

    await next_handler(message)


class RawClient:
    protocol = None  # type: Optional[Protocol]
    raw_handlers = None  # type: List[Callable]

    _event_handlers = None  # type: Dict[str, List[Callable]]
    _events = None  # type: Dict[str, asyncio.Event]

    def __init__(self, host: str, port: int, *,
                 encoding: str = "UTF-8", ssl: bool = True,
                 loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        self.host = host
        self.port = port
        self.ssl = ssl
        self.encoding = encoding
        self.raw_handlers = []

        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop

        self._event_handlers = collections.defaultdict(list)
        self._events = collections.defaultdict(
            lambda: asyncio.Event(loop=self.loop))

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        """Do not change the event loop for a client"""
        return self._loop

    def handle_raw(self, message: str) -> None:
        handle = process(self.raw_handlers, message)
        self.loop.create_task(handle)

    def send_raw(self, message: str) -> None:
        if not self.protocol:
            raise RuntimeError("Not connected")
        self.protocol.write(message)

    async def connect(self) -> None:
        """Open a connection to the defined server."""
        def protocol_factory() -> Protocol:
            return Protocol(client=self)

        _, protocol = await self.loop.create_connection(
            protocol_factory,
            host=self.host,
            port=self.port,
            ssl=self.ssl
        )  # type: Tuple[Any, Any]
        if self.protocol:
            self.protocol.close()
        self.protocol = protocol
        # TODO: Delete the following code line. It is currently kept in order
        # to not break the current existing codebase. Removing it requires a
        # heavy change in the test codebase.
        protocol.client = self
        self.trigger("client_connect")

    async def disconnect(self) -> None:
        """Close the connection to the defined server."""
        if self.protocol:
            self.protocol.close()

    def trigger(self, event: str, **kwargs: Any) -> None:
        """Trigger all handlers for an event to (asynchronously) execute"""
        event = event.upper()
        for func in self._event_handlers[event]:
            self.loop.create_task(func(**kwargs))
        # This will unblock anyone that is awaiting on the next loop update,
        # while still ensuring the next `await client.wait(event)` doesn't
        # immediately fire.
        async_event = self._events[event]
        async_event.set()
        async_event.clear()

    async def wait(self, event: str) -> str:
        await self._events[event.upper()].wait()
        return event

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
        self._event_handlers[event.upper()].append(wrapped)
        # Always return original
        return func

    def _connection_lost(self, protocol: asyncio.Protocol) -> None:
        # Ignore connection_lost for old connections
        if protocol is self.protocol:
            self.trigger("client_disconnect")
            self.protocol = None


class Client(RawClient):
    def __init__(self, host: str, port: int, *,
                 encoding: str = "utf-8", ssl: bool = True,
                 loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        """

        :param host: The IRC server address to connect to.
        :param port: The port of the IRC server.
        :param encoding: The character encoding to use.  Default is utf-8.
        :param ssl:
            Whether SSL should be used while connecting.
            Default is True.
        :param loop:
            The even loop to use.
            Defaults is ``asyncio.get_event_loop()``.
        """
        super().__init__(host, port, encoding=encoding, ssl=ssl, loop=loop)
        self.raw_handlers.append(rfc2812_handler(self))

    def send(self, command: str, **kwargs: Any) -> None:
        """
        Send a message to the server.

        .. code-block:: python

            client.send("nick", nick="weatherbot")
            client.send("privmsg", target="#python", message="Hello, World!")

        """
        packed_command = pack_command(command, **kwargs).strip()
        self.send_raw(packed_command)


rfc2812_log = logging.getLogger('bottom.rfc2812_handler')


def rfc2812_handler(client: RawClient) -> Callable:
    async def handler(next_handler: Callable, message: str) -> None:
        try:
            event, kwargs = unpack_command(message)
            client.trigger(event, **kwargs)
        except ValueError:
            rfc2812_log.debug("Failed to parse line >>> {}".format(message))
        await next_handler(message)
    return handler
