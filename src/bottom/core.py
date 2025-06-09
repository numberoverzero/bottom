from __future__ import annotations

import asyncio
import collections
import ssl
import typing as t

from bottom import util

__all__ = ["BaseClient", "ClientMessageHandler", "NextMessageHandler", "Protocol"]

# Always write the full \r\n per spec, but accept \n when reading
DELIM = b"\r\n"
DELIM_COMPAT = b"\n"

ProtocolMessageHandler = t.Callable[[str], None]
ConnectionLostHandler = t.Callable[["Protocol", Exception | None], None]


def default_connection_lost_handler(protocol: Protocol, exc: Exception | None) -> None:  # pragma: no cover
    pass


class Protocol(asyncio.Protocol):
    transport: asyncio.WriteTransport | None = None
    on_message: ProtocolMessageHandler
    on_connection_lost: ConnectionLostHandler
    buffer: bytes = b""
    encoding: str

    def __init__(
        self,
        handle_message: ProtocolMessageHandler,
        handle_connection_lost: ConnectionLostHandler | None,
        encoding: str | None,
    ) -> None:
        self.on_message = handle_message
        if handle_connection_lost is None:  # pragma: no cover
            handle_connection_lost = default_connection_lost_handler
        self.on_connection_lost = handle_connection_lost
        if encoding is None:  # pragma: no cover
            encoding = "utf-8"
        self.encoding = encoding

    # note: same way typeshed handles the subclass typing problem
    # https://github.com/python/typeshed/blob/8f5a80e7b741226e525bd90e45496b8f68dc69b6/stdlib/asyncio/protocols.pyi#L24
    def connection_made(self, transport: asyncio.WriteTransport) -> None:  # type: ignore[override]
        if self.transport:
            raise RuntimeError(f"{self} tried to connect to {transport} but already connected to {self.transport}")
        self.transport = transport

    def connection_lost(self, exc: Exception | None) -> None:
        transport = self.transport
        if transport:
            self.transport = None
            self.on_connection_lost(self, exc)
            if not transport.is_closing():
                transport.close()

    def data_received(self, data: bytes) -> None:
        self.buffer += data
        # All but the last result of split should be pushed into the
        # client.  The last will be b"" if the buffer ends on b"\n"
        *lines, self.buffer = self.buffer.split(DELIM_COMPAT)
        for line in lines:
            message = line.decode(self.encoding, "ignore").strip()
            self.on_message(message)

    def write(self, message: str) -> None:
        """immediately writes the message as a complete line; there is no write buffering"""
        if not self.transport:
            raise RuntimeError(f"Protocol {self} not connected")
        message = message.strip()
        data = message.encode(self.encoding) + DELIM
        self.transport.write(data)

    def close(self) -> None:
        if self.transport:
            self.transport.close()

    @property
    def is_closed(self) -> bool:
        return self.transport is None


class EventHandler:
    event_waiters: dict[str, asyncio.Event]
    event_handlers: dict[str, list[t.Callable[..., t.Coroutine[t.Any, t.Any, t.Any]]]]

    def __init__(self) -> None:
        self.event_handlers = collections.defaultdict(list)
        self.event_waiters = collections.defaultdict(asyncio.Event)

    @t.overload
    def on[**P, R](self, event: str, fn: None = None) -> util.Decorator[P, R]: ...
    @t.overload
    def on[**P, R](self, event: str, fn: t.Callable[P, R]) -> t.Callable[P, R]: ...

    def on[**P, R](self, event: str, fn: t.Callable[P, R] | None = None) -> util.Decorator[P, R] | t.Callable[P, R]:
        """
        Decorate a function to be invoked when the given event occurs.

        The function may be a coroutine.  Your function should accept **kwargs
        in case an event is triggered with unexpected kwargs.

        ```
        import asyncio
        import bottom

        client = bottom.Client(...)
        @client.on("test")
        async def func(one, two, **kwargs):
            print(one)
            print(two)
            print(kwargs)


        async def test():
            task = events.trigger("test", **{"one": 1, "two": 2, "extra": "foo"})
            print("triggered event")
            await task

        asyncio.run(test())

        # prints:
        # 1
        # 2
        # {'extra': 'foo'}
        # triggered event
        ```
        """

        def decorator(f: t.Callable[P, R]) -> t.Callable[P, R]:
            async_fn = util.ensure_async_fn(f)
            self.event_handlers[event.strip().upper()].append(async_fn)
            return f

        return decorator if fn is None else decorator(fn)

    def trigger(self, event: str, **kwargs: t.Any) -> asyncio.Task:
        """
        Trigger all handlers for an event to asynchronously execute.

        You can optionally await the returned task to wait until all handlers
        have run.

        Use `await client.wait(event)` to wait for this event to trigger.

        ```
        # waiting for handlers to run
        async def simulate_disconnect():
            print("simulating disconnect")
            handlers = client.trigger("client_disconnect")
            await handlers
            print("all disconnect handlers finished")

        # fire and forget
        async def custom_signal():
            client.trigger("my-signal", some_arg=3, data=b"data")
            print("triggered my-signal, not waiting for handlers to complete")
        ```
        """
        event = event.strip().upper()
        # note: create the asyncio.Event before creating the tasks below
        async_event = self.event_waiters[event]

        tasks = []
        for func in self.event_handlers[event]:
            tasks.append(util.create_task(func(**kwargs)))

        async def toggle() -> None:
            # note: without this asyncio.sleep(0), anything that started waiting
            # in this loop tick won't see the event fire.
            await asyncio.sleep(0)
            async_event.set()
            async_event.clear()

        util.create_task(toggle())
        return util.join_tasks(tasks)

    async def wait(self, event: str) -> str:
        """
        Wait for an event to be triggered.  Returns the name of the event that was awaited.

        Useful for blocking an async task until an event occurs, like join or disconnect:

        ```
        async def reconnect():
            while True:
                print("waiting for disconnect event")
                await client.wait("client_disconnect")

                print("reconnecting...")
                await client.connect()
                client.send("nick", nick="mybot")
                client.send("pass", password="hunter2")

                print("reconnected!")
        ```
        """
        await self.event_waiters[event.strip().upper()].wait()
        return event


type NextMessageHandler = t.Callable[[str], t.Coroutine[t.Any, t.Any, t.Any]]
type ClientMessageHandler = t.Callable[[NextMessageHandler, str], t.Coroutine[t.Any, t.Any, t.Any]]


class BaseClient(EventHandler):
    message_handlers: list[ClientMessageHandler]
    """
    Each message_handler must be an async function that takes a next_handler in
    the handler chain, and the message to handle.

    Note that you do not have to invoke the next handler:

    ```
    async def ignore_with_prefix(
        next_handler: bottom.NextMessageHandler, message: str
    ) -> None:
        if message.startswith("ignore:"):
            print(f"ignoring message {message}")
        else:
            print(f"processing message {message}")
            await next_handler(message)
    ```
    """

    protocol: Protocol | None = None
    encoding: str
    ssl: ssl.SSLContext | bool
    host: str
    port: int

    def __init__(self, host: str, port: int, *, encoding: str = "UTF-8", ssl: bool | ssl.SSLContext = True) -> None:
        super().__init__()
        self.host = host
        self.port = port
        self.encoding = encoding
        self.ssl = ssl
        self.message_handlers = []

    async def connect(self) -> None:
        if self.protocol and not self.protocol.is_closed:
            return
        loop = asyncio.get_running_loop()
        _transport, protocol = await loop.create_connection(
            make_protocol_factory(self), host=self.host, port=self.port, ssl=self.ssl
        )
        if self.protocol:
            protocol.close()
            return
        self.protocol = protocol
        self.trigger("client_connect")

    async def disconnect(self) -> None:
        if self.protocol:
            self.protocol.close()

    def send_message(self, message: str) -> None:
        if not self.protocol:
            raise RuntimeError("Not connected")
        self.protocol.write(message)


def make_protocol_factory(client: BaseClient) -> t.Callable[[], Protocol]:
    def handle_connection_lost(protocol: Protocol, exc: Exception | None) -> None:
        if protocol is client.protocol:
            client.trigger("client_disconnect")
            client.protocol = None

    def handle_message(message: str) -> None:
        util.stack_process(client.message_handlers, message)

    def protocol_factory() -> Protocol:
        return Protocol(
            handle_message=handle_message,
            handle_connection_lost=handle_connection_lost,
            encoding=client.encoding,
        )

    return protocol_factory
