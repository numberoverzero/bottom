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

ProtocolMessageHandler = t.Callable[[bytes], None]
ConnectionLostHandler = t.Callable[["Protocol", Exception | None], None]


def default_connection_lost_handler(protocol: Protocol, exc: Exception | None) -> None:  # pragma: no cover
    pass


class Protocol(asyncio.Protocol):
    transport: asyncio.WriteTransport | None = None
    on_message: ProtocolMessageHandler
    on_connection_lost: ConnectionLostHandler
    buffer: bytes = b""

    def __init__(
        self,
        handle_message: ProtocolMessageHandler,
        handle_connection_lost: ConnectionLostHandler | None,
    ) -> None:
        self.on_message = handle_message
        if handle_connection_lost is None:  # pragma: no cover
            handle_connection_lost = default_connection_lost_handler
        self.on_connection_lost = handle_connection_lost

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
            self.on_message(line.strip())

    def write(self, message: bytes) -> None:
        """immediately writes the message as a complete line; there is no write buffering"""
        # can't use self.is_closed or type checkers complain at self.transport.write() below
        if self.transport is None or self.transport.is_closing():
            raise RuntimeError(f"Protocol {self} not connected")
        self.transport.write(message.strip() + DELIM)

    def close(self) -> None:
        if self.transport:
            self.transport.close()

    def is_closing(self) -> bool:
        return self.transport is None or self.transport.is_closing()


class EventHandler:
    _event_futures: collections.defaultdict[str, asyncio.Future[dict]]
    _event_handlers: dict[str, list[t.Callable[..., t.Coroutine[t.Any, t.Any, t.Any]]]]

    def __init__(self) -> None:
        self._event_handlers = collections.defaultdict(list)
        self._event_futures = collections.defaultdict(asyncio.Future)

    @t.overload
    def on[**P, R](self, event: str, fn: None = None) -> util.Decorator[P, R]: ...
    @t.overload
    def on[**P, R](self, event: str, fn: t.Callable[P, R]) -> t.Callable[P, R]: ...

    def on[**P, R](self, event: str, fn: t.Callable[P, R] | None = None) -> util.Decorator[P, R] | t.Callable[P, R]:
        """
        Decorate a function to handle an event.

        See :ref:`Events<Events>` for a list of supported rfc2812 events.

        When an event is triggered, either by the default rfc2812 handler or by your code, all functions registered
        to that event are triggered.  Your handlers should always accept ``**kwargs`` in case unexpected kwargs are
        included when the event is triggered.

        Event names ignore leading space, trailing space, and case; both when registering and triggering.  So
        ``" bEgIn  "`` is registered and triggered as ``"BEGIN"``.  Since you can pass any event name, it's easy to
        :ref:`extend<Extensions>` a client with your own signals.

        You don't need to unpack all arguments, but you should always include
        ``**kwargs`` to collect the rest::

            @client.on("privmsg")
            async def standby(message, **kwargs):
                if message == codeword:
                    await execute_heist()

        While you should prefer ``async`` handlers, it's not required.  Synchronous functions will be wrapped in an
        async handler so that the event loop is available, which means you can use ``asyncio.create_task`` without
        checking for a running loop::

            @client.on("privmsg")
            def handle(message, **kwargs):
                print(message)

            @client.on("privmsg")
            async def handle(message, **kwargs):
                await async_logger.log(message)

        .. note::

            The original function is returned, so you can chain decorators without introducing an async wrapper to your
            code::

                def original(message, **kwargs):
                    asyncio.create_task(f"saw msg {message}")

                wrapped = client.on("privmsg")(original)
                assert wrapped is original

        Finally, you can trigger and catch your your own events.  For example, to forward ``SIGINT``::

            import signal
            signal.signal(
                signal.SIGINT,
                lambda *a: client.trigger("my.plugin.sigint")
            )


            @client.on("my.plugin.sigint")
            async def handle(**kwargs):
                print("saw SIGINT")
                await send_farewells(client, db.get_friends_list())
                await client.disconnect()
        """

        def decorator(f: t.Callable[P, R]) -> t.Callable[P, R]:
            async_fn = util.ensure_async_fn(f)
            self._event_handlers[event.strip().upper()].append(async_fn)
            return f

        return decorator if fn is None else decorator(fn)

    def trigger(self, event: str, **kwargs: t.Any) -> asyncio.Task:
        """
        Manually trigger an event, either a :ref:`supported rfc2812 command<Commands>` or a custom event name.

        Trigger returns a task which you can ``await`` to block until all registered handlers for the event have
        completed.  You do not have to wait for this task or keep a reference to it.


        For example, if you migrate to a third-party extension that expects "!help" but your original command was
        "!commands" then you can use the following handler to inform users *and* forward to the new handler::

            @client.on("privmsg")
            async def help_compat(nick, target, message, **kwargs):
                if message != "!commands": return

                # notify
                await client.send(
                    "privmsg", target=nick,
                    message="note: !commands was renamed to !help in 1.2")

                # forward
                client.trigger(
                    "privmsg", nick=nick,
                    target=target, message="!help")


        Because the ``@on`` decorator returns the original function, you can register a handler for multiple events.
        It's especially important to use ``**kwargs`` to handle different keywords for each event::

            @client.on("privmsg")
            @client.on("join")
            @client.on("part")
            async def handle(target, message=None, channel=None, **kwargs):
                if channel:
                    client.trigger("my.plugin.events.channel", channel=channel, **kwargs)
                elif message:
                    client.trigger("my.plugin.events.messages", message=message, **kwargs)

        If you want to trigger an event and then wait until all handlers for that event
        have run, you can ``await`` the returned task::

            complete = []

            @client.on("my.event")
            async def fast_processor(data: str, **kwargs):
                await asyncio.sleep(1)
                complete.append(f"fast {data}")

            @client.on("my.event")
            async def slow_processor(data: str, **kwargs):
                await asyncio.sleep(2)
                complete.append(f"slow {data}")

            @client.on("part")
            async def handle_part(channel: str, **kwargs):
                complete.clear()
                await client.trigger("my.event", data=channel)
                assert complete == [f"slow {channel}", f"fast {channel}"]
        """
        event = event.strip().upper()
        kwargs["__event__"] = event

        tasks = []
        for func in self._event_handlers[event]:
            tasks.append(util.create_task(func(**kwargs)))

        async def toggle() -> None:
            # note: without this asyncio.sleep(0), anything that started waiting
            # in this loop tick won't see the event fire.
            await asyncio.sleep(0)
            # note: defaultdict.pop still raises KeyError.
            # direct lookup followed by del ensures we get any existing future, and that
            # we clear the slot for the next waiters
            fut = self._event_futures[event]
            assert not fut.done()
            del self._event_futures[event]
            fut.set_result({**kwargs})

        util.create_task(toggle())
        return util.join_tasks(tasks)

    async def wait(self, event: str) -> dict:
        """
        Wait for an event to be triggered.  Returns a dict including the kwargs the event was triggered with, as
        well as the name of the event in the ``"__event__"`` key.

        See :ref:`Events<Events>` for a list of supported rfc2812 events.

        Useful for blocking an async task until an event occurs, like join or disconnect::

            async def reconnect():
                while True:
                    print("waiting for disconnect event")
                    await client.wait("client_disconnect")

                    print("reconnecting...")
                    await client.connect()
                    await client.send("nick", nick="mybot")
                    await client.send("pass", password="hunter2")

                    print("reconnected!")

        You can inspect the kwargs that the event was triggered with, and get the event name from ``"__event__"``::

            async def wait_join():
                client.join(channel="#chan")
                kwargs = await client.wait("join")

                assert kwargs["__event__"] == "join"
                print(f"complete join event: {kwargs}")

        You can use :func:`asyncio.wait_for` or :func:`asyncio.timeout` to add a timeout to your wait::

            async def connect()
                try:
                    with asyncio.timeout(5):
                        await client.connect()
                except TimeoutError:
                    print("failed to connect within 5 seconds, is the server available?")


        Use :meth:`wait_for<bottom.wait_for>` to wait for multiple events, either the first to complete or all.
        """
        return await self._event_futures[event.strip().upper()]


# TODO: sphinx doesn't support PEP 695 types yet
# https://github.com/sphinx-doc/sphinx/issues/11561
# https://github.com/sphinx-doc/sphinx/pull/13508

type NextMessageHandler[T: BaseClient] = t.Callable[[T, bytes], t.Coroutine[t.Any, t.Any, t.Any]]
"""
Type hint for an async function that takes a message to process.

This is the type of the first argument in a message handler::

    from bottom import Client, ClientMessageHandler, NextMessageHandler

    class MyClient(Client):
        pass

    async def handle_message(next_handler: NextMessageHandler[MyClient], client: MyClient, message: bytes):
        print(f"I saw a message: {message.decode()}")
        await next_handler(client, message)

see :attr:`message_handlers<bottom.Client.message_handlers>` for details, or :ref:`Extensions<Extensions>` for
examples of customizing a :class:`Client<bottom.Client>`'s functionality.
"""

# TODO: sphinx doesn't support PEP 695 types yet
# https://github.com/sphinx-doc/sphinx/issues/11561
# https://github.com/sphinx-doc/sphinx/pull/13508

type ClientMessageHandler[T: BaseClient] = t.Callable[
    [NextMessageHandler[T], T, bytes], t.Coroutine[t.Any, t.Any, t.Any]
]
"""
Type hint for an async function that processes a message, and may call the next handler in the chain.

This is the type of the entire message handler::

    from bottom import Client, ClientMessageHandler, NextMessageHandler

    class MyClient(Client):
        pass

    async def handle_message(next_handler: NextMessageHandler[MyClient], client: MyClient, message: bytes):
        print(f"I saw a message: {message.decode()}")
        await next_handler(client, message)

    handler: ClientMessageHandler[MyClient] = handle_message

see :attr:`message_handlers<bottom.Client.message_handlers>` for details, or :ref:`Extensions<Extensions>` for
examples of customizing a :class:`Client<bottom.Client>`'s functionality.
"""


class BaseClient(EventHandler):
    message_handlers: list[ClientMessageHandler]
    """List of message handlers that runs on each incoming IRC line from the server.

    The first handler is passed the ``next_handler`` in the chain as well as the ``client`` and ``message``.  The
    handler can choose to process the message, and/or invoke the next handler, or do nothing.

    The basic structure of a handler is::

        from bottom import Client, NextHandler

        async def handle_message(next_handler: NextHandler[Client], client: Client, message: bytes) -> None:
            print("before")
            await next_handler(client, message)
            print("after")

    By default, every client is configured with a ``rfc2812_handler`` which unpacks
    :ref:`supported rfc2812 commands<Commands>` into events and triggers them, connecting them to handlers you've
    registered with :meth:`Client.on<bottom.Client.on>`

    You can disable the default functionality by removing that handler::

        from bottom import Client
        client = Client(host="localhost", port=443)
        client.message_handlers.clear()

    You can add your own handlers before or after this one, or replace it::

        from bottom import Client, NextMessageHandler

        async def print_everything(next_handler: NextMessageHandler[Client], client: Client, message: bytes) -> None:
            print(f"incoming message: {message.decode()}")
            await next_handler(client, message)

        client = Client(host="localhost", port=443)
        # run after other handlers
        client.message_handlers.append(print_everything)

    Message handlers don't have to call the next handler, and don't have to pass the same message to the next handler::

        from bottom import Client, NextMessageHandler

        async def uno_handler(next_handler: NextMessageHandler[Client], client: Client, message: bytes) -> None:
            if message.startswith(b"reverse:"):
                message = message[len(b"reverse:"):]
                print(f"reversing {message.decode()}")
                await next_handler(client, message[::-1])
            elif message.startswith(b"skip:"):
                message = message[len(b"skip:"):]
                print(f"skipping: {message.decode()}")
            else:
                print("passing message through unchanged")
                await next_handler(client, message)

        # run before other handlers
        client.message_handlers.insert(0, uno_handler)

    Modifying :attr:`message_handlers<bottom.Client.message_handlers>` is the primary way to extend or customize the
    client.  For examples of writing your own router, or replacing these handlers, see the :ref:`extensions<Extensions>`
    section of the user guide.

    .. note::

        Each incoming message is handled using a copy of the handlers when the message arrived. Changes to the list do
        not affect handling of that message::

            async def remove_other_handlers(next_handler, client, message):
                client.message_handlers.clear()
                await next_handler(client, message)  # still uses original handlers
    """

    _protocol: Protocol | None = None
    _encoding: str
    _ssl: ssl.SSLContext | bool
    _host: str
    _port: int

    def __init__(self, host: str, port: int, *, encoding: str = "utf-8", ssl: bool | ssl.SSLContext = True) -> None:
        super().__init__()
        self._host = host
        self._port = port
        self._encoding = encoding
        self._ssl = ssl
        self.message_handlers = []

    def is_closing(self) -> bool:
        """Return True if the Client is closing or closed."""
        return self._protocol is None or self._protocol.is_closing()

    async def connect(self) -> None:
        """Connect to the server.

        On successful connection, triggers a ``"client_connect"`` event.

        Returns immediately if the client already has a non-closing connection.  When multiple connect calls are in
        progress at once, only the first call to establish a connection will trigger a ``"client_connect"`` and the
        others will silently disconnect their parallel connections to the server.

        Usage::

            async def main():
                await client.connect()
                try:
                    await client.wait("client_disconnect")
                except asyncio.CancelledError:
                    await client.disconnect()
            asyncio.run(main())

            @client.on("client_disconnect")
            async def reconnect(**kwargs):
                # don't reconnect immediately
                await asyncio.sleep(3)

                await client.connect()
                # Now that we're connected, let everyone know
                await client.send("privmsg", target=client.channel, message="I'm back.")


        Or to schedule the connect without blocking::

            from bottom.util import create_task

            @client.on("client_disconnect")
            async def reconnect(**kwargs):
                async def run():
                    await asyncio.sleep(3)
                    await client.connect()

                # note: you could use asyncio.create_task(), but it may get gc'd if you don't keep a ref.
                #   bottom.util.create_task handles this for you.
                #   see: https://docs.python.org/3/library/asyncio-task.html#asyncio.create_task
                create_task(run())
                print("Reconnect scheduled.")
        """
        if not self.is_closing():
            return
        loop = asyncio.get_running_loop()
        _transport, protocol = await loop.create_connection(
            make_protocol_factory(self), host=self._host, port=self._port, ssl=self._ssl
        )
        if self._protocol:
            protocol.close()
            return
        self._protocol = protocol
        self.trigger("client_connect")

    async def disconnect(self) -> None:
        """Disconnect from the server.

        On successful disconnection, triggers a ``"client_disconnect"`` event.

        Returns immediately if the client is already disconnected or disconnecting.  When multiple connect calls are in
        progress at once, only the first call to disconnect the client will trigger a ``"client_disconnect"``.

        Usage::

            @client.on("privmsg")
            async def disconnect_bot(nick, message, **kwargs):
                if nick == "myNick" and message == "disconnect:hunter2":
                    await client.disconnect()
                    logger.log("disconnected client.")
        """
        if self._protocol:
            self._protocol.close()
            assert self._protocol.is_closing()
            try:
                await self.wait("client_disconnect")
            except asyncio.CancelledError:  # pragma: no cover
                pass

    async def send_message(self, message: str) -> None:
        """Send a complete IRC line without modification.

        To easily send an rfc 2812 message, consider :meth:`Client.send<bottom.Client.send>`

        ::

            import base64

            async def send_encoded(image: bytes):
                encoded_str = base64.b64encode(image).decode()
                await client.send_message(f"IMG :{encoded_str}")

        """
        if not self._protocol or self._protocol.is_closing():
            raise RuntimeError("Not connected")
        self._protocol.write(message.encode(self._encoding))


def make_protocol_factory(client: BaseClient) -> t.Callable[[], Protocol]:
    def handle_connection_lost(protocol: Protocol, exc: Exception | None) -> None:
        if protocol is client._protocol:
            client.trigger("client_disconnect")
            client._protocol = None

    def handle_message(message: bytes) -> None:
        util.stack_process(client.message_handlers, client, message)

    def protocol_factory() -> Protocol:
        return Protocol(
            handle_message=handle_message,
            handle_connection_lost=handle_connection_lost,
        )

    return protocol_factory
