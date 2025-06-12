.. _Extensions:

Extending the Client
^^^^^^^^^^^^^^^^^^^^

bottom doesn't use clever import hooks or implicit magic to find and load plugins or extensions.

Extending the Client is mainly done by registering :meth:`event handlers<bottom.Client.on>`,
:meth:`triggering<bottom.Client.trigger>`, and :meth:`waiting<bottom.Client.wait>` on events; or modifying the client's
:attr:`message_handlers<bottom.Client.message_handlers>`.


Keepalive
=========

Instead of writing the same ``PING`` handler everywhere, a reusable plugin:

.. code-block:: python

    # my_plugin.py
    from bottom import Client
    async def keepalive(client: Client) -> Client:
        @client.on("ping")
        async def handle(message: str, **kwargs):
            print(f"<<< ping {message}")
            await client.send("pong", message=message)
            print(f">>> pong {message}")
        return client

That's it!  And to use it:

.. code-block:: python

    import bottom
    from my_plugin import keepalive

    client = bottom.Client(...)
    keepalive(client)

.. _ex-plugins:

Plugin Registry
===============

*(The full source for this extension is available at examples/registry.py)*

In the keepalive example above, we're really just using partial application of :meth:`Client.on<bottom.Client.on>`.
We can use that idea and a ``dict`` to make a plugin registry!  Let's start with the core ``Registry`` class.

One additional complexity over the previous example is getting a reference to the client within the function.  We
solve that below by passing the client as the first argument to the handler; our ``keepalive`` from above will be
slightly different when we're ready to decorate it.

.. code-block:: python

    class Registry:
        plugins: dict[str, t.Callable[[Client], None]]

        def __init__(self) -> None:
            self.plugins = {}

        def register[**P](self, event: str, fn: HandlerTakesClient, name: str | None = None) -> None:
            assert asyncio.iscoroutinefunction(fn), f"{fn} must be async to register"

            def apply(client: Client) -> None:
                async def handle(*a: P.args, **kw: P.kwargs) -> None:
                    await fn(client, *a, **kw)

                client.on(event)(handle)

            if isinstance(name, str):
                name = name.strip().upper()
            name = name or fn.__name__
            if name in self.plugins:
                raise RuntimeError(f"tried to register {fn} as {name!r} but that name is taken.")

            self.plugins[name] = apply

        def enable(self, client: Client, *plugin_names: str) -> None:
            for event in plugin_names:
                apply = self.plugins[event.strip().upper()]
                apply(client)

We'll also need some imports and a typedef for that ``HandlerTakesClient`` type:

.. code-block:: python

    import asyncio
    import typing as t

    from bottom import Client

    type HandlerTakesClient[**P] = t.Callable[t.Concatenate[Client, P], t.Coroutine]

The type ``HandlerTakesClient`` represents an async function that takes a :class`Client<bottom.Client>` as its
first argument, and we don't care about the rest of its signature.

The ``register`` function does the heavy lifting through two functions:

* the innermost ``handle`` function is going to intercept the real function, and inject the client as its first
  argument.  this way, we can define our plugins without knowing our clients ahead of time.  That means our
  ``keepalive`` handler from the previous example will become:

  .. code-block:: python

      async def keepalive(client: Client, message: str, **kwargs):
          print(f"<<< ping {message}")
          await client.send("pong", message=message)
          print(f">>> pong {message}")

      registry = Registry()
      registry.register("ping", keepalive, name="my.keepalive.plugin")

* the inner ``apply`` function inside ``register`` is just a function that takes a client to create the ``handle``
  wrapper above.  this is because we don't know the client at the time we're registering the function.  Instead,
  this ``apply`` function is stored in the Registry's ``plugins`` dict for later application.
* we store the ``apply`` wrapper under either a provided name, or fall back to the function's name.

Finally, we can apply each of these plugins to a client with ``enable``:

.. code-block:: python

    import bottom
    registry = Registry()

    client = bottom.Client(...)
    registry.enable(client, "my.keepalive.plugin")

To make things a little easier on ourselves, we can add a default registry and make an ``@register`` decorator that
takes the registry, or falls back to the default registry:

.. code-block:: python

    GLOBAL_REGISTRY = Registry()

    def register[T: HandlerTakesClient](
        event: str, *, registry: Registry = GLOBAL_REGISTRY, name: str | None = None
    ) -> t.Callable[[T], T]:
        def register_plugin(fn: T) -> T:
            registry.register(event, fn, name)
            return fn

        return register_plugin


    def enable(client: Client, *plugin_names: str, registry: Registry = GLOBAL_REGISTRY) -> None:
        registry.enable(client, *plugin_names)


Now, our plugin and client setup look like this:

.. code-block:: python

    # plugins.py
    from registry import register

    @register("ping", name="my.keepalive.plugin")
    async def keepalive(client: Client, message: str, **kwargs):
          print(f"<<< ping {message}")
          await client.send("pong", message=message)
          print(f">>> pong {message}")


    # main.py
    import plugin  # so that our plugins are registered
    from bottom import Client
    from registry import enable

    client = Client(host=..., port=...)
    enable(client, "my.keepalive.plugin")


Only Handle Whole Lines
=======================

If you don't want IRC command packing and unpacking then you can remove the default handler
and insert one that simply forwards the entire line to your handler function:

.. code-block:: python

    from __future__ import annotations

    from bottom import Client, NextMessageHandler


    class DirectClient(Client):
        def __init__(self, *a, **kw) -> None:
            super().__init__(*a, **kw)
            self.message_handlers.clear()
            self.message_handlers.append(self.my_line_handler)

        async def my_line_handler(
            self, next_handler: NextMessageHandler, client: DirectClient, line: bytes,
        ) -> None:
            # TODO process the whole IRC line here
            # or, pass it somewhere else with self.trigger("...", line=line)
            print(f"got whole irc line in bytes: {line}")


Replication
===========

We can set up multiple clients to replicate messages from one server to another.  There are a few ways to do this, the
most obvious being the same :meth:`Client.on<bottom.Client.on>` handling we've used before:


.. code-block:: python

    from bottom import Client


    def make_replicator(watcher: Client, replicas: list[Client], channel: str):
        @watcher.on("privmsg")
        async def forward_messages(nick, target, message, **kw):
            if target != channel:
                return
            message = f"{nick}: {message}"
            for replica in replicas:
                if replica.is_closing():
                    continue
                await replica.send("privmsg", target=channel, message=message)

This is clear enough but what if we wanted to treat the watcher as more of a router? Anything it forwards to the
replicas *shouldn't* be emitted as events from the watcher itself.  We can choose which PRIVMSG will be triggered on
the watcher, and which will be forwarded to the listeners; and we'll never forward pings.

Filtering before messages reach :meth:`Client.on<bottom.Client.on>` handlers is done
through a :data:`ClientMessageHandler<bottom.ClientMessageHandler>`:


.. code-block:: python

    class RoutingClient(Client):
        nick: str = "replicate-bot"
        audit_log: str = "#replica-audit"
        listeners: list[Client]

        def __init__(self, *a, **kw) -> None:
            super().__init__(*a, **kw)
            self.listeners = []
            self.message_handlers.insert(0, possibly_reroute)

        def should_reroute(self, message: str) -> bool:
            # TODO impl parse_cmd
            command = parse_cmd(message)
            if command not in ["PRIVMSG", "PING"]:
                return True
            # TODO impl parse_target
            target = parse_target(message)
            if target != self.nick:
                return True
            return False

        def rewrite(self, message: str) -> list[str]:
            # TODO - replace nick, change target, add lines?
            # for now just forward the original message, and
            # write a copy into the audit log
            return [
                f"PRIVMSG {self.audit_log} :{message}",
                message,
            ]

        async def broadcast(self, message: str):
            for listener in self.listeners:
                if listener.is_closing():
                    continue
                await listener.send_message(message)


    async def possibly_reroute(
        next_handler: NextMessageHandler[RoutingClient], client: RoutingClient, message: bytes
    ) -> None:
        as_str = message.decode(client._encoding)
        if client.should_reroute(as_str):
            messages = client.rewrite(as_str)
            for each in messages:
                await client.broadcast(each)
        else:
            await next_handler(client, message)


And to set up handlers so we can still control the routing client:

.. code-block:: python

    import asyncio

    client = RoutingClient(...)
    client.listeners.extend(load_listeners())


    @client.on("ping")
    async def keepalive(message, **kw):
        await client.send("pong", message=message)


    @client.on("privmsg")
    async def handle_command(nick, target, message, **kw):
        rc = client
        # because all other privmsg were filtered out,
        # we know this is sent directly to the routing client
        assert target == rc.nick

        if message != "shutdown":  # TODO impl other commands
            return

        if nick == "admin":
            notice = f"PRIVMSG {rc.audit_log} :!{rc.nick} shutting down"
            await rc.broadcast(notice)
            tasks = [c.disconnect() for c in [rc, *rc.listeners]]
            await asyncio.wait(tasks)
        else:
            notice = f"PRIVMSG {rc.audit_log} :!{nick} tried to call shutdown"
            await rc.broadcast(notice)


Pattern matching
================

*(The full source for this extension is available at examples/regex.py)*

We can write a simple wrapper class to annotate functions to handle PRIVMSG matching a regex.
To keep the interface simple, we can use bottom's annotation pattern and pass the regex to match.

In the following example, we'll define a handler that echos whatever a user asks for, if it's in the correct format:

.. code-block:: python


    import re
    import bottom
    from regex import Router

    client = bottom.Client(host=..., port=...)
    router = Router(client)


    @router.route(r"^bot, say (\w+) please$")
    async def echo(self, nick: str, target: str, match: re.Match, **kwargs):
        if target == router.nick:
            # respond in a direct message
            target = nick
        await client.send("privmsg", target=target, message=match.group(1))


The router is fairly simple: a ``route`` function that decorates a function, and a handler registered to the client's
PRIVMSG event:

.. code-block:: python

    import asyncio
    import re
    import typing as t

    from bottom import Client
    from bottom.util import create_task


    class Router(object):
        def __init__(self, client: Client) -> None:
            self.client = client
            self.routes = {}
            client.on("privmsg")(self._handle_privmsg)

        async def _handle_privmsg(self, **kwargs: t.Any) -> None:
            """client callback entrance"""
            for regex, (func, pattern) in self.routes.items():
                match = regex.match(kwargs["message"])
                if match:
                    kwargs.update({"match": match, "pattern": pattern})
                    create_task(func(**kwargs))

        def route[T: t.Coroutine](self, pattern: str | re.Pattern[str]) -> t.Callable[[T], T] | T:
            def decorator(fn: T) -> T:
                assert asyncio.iscoroutinefunction(fn), f"{fn} must be async to register"
                if isinstance(pattern, str):
                    compiled = re.compile(pattern)
                else:
                    compiled = pattern
                self.routes[compiled] = (fn, compiled.pattern)
                return fn

            return decorator


.. _ex-encryption:

Full message encryption
=======================

*(The full source for this extension is available at examples/encryption.py)*

This is a more complex example of a :data:`ClientMessageHandler<bottom.ClientMessageHandler>` where messages are
encrypted and then base64 encoded.  On the wire their only conformance to the IRC protocol is a newline terminating
character.  This is enough to build an extension to transparently encrypt data.

We're going to implement against the following encryption stub, instead of whichever cryptography library you would
actually use.  Selecting a cryptography library is out of scope for this example.

.. code-block:: python

    class EncryptionContext:
        async def encrypt(self, data: bytes) -> bytes:
            ...

        async def decrypt(self, data: bytes) -> bytes:
            ...

We'll handle incoming messages with a :data:`ClientMessageHandler<bottom.ClientMessageHandler>`:

.. code-block:: python

    import base64
    from bottom import NextMessageHandler

    async def decrypt_message(next_handler: NextMessageHandler[EncryptingClient], client: EncryptingClient, message: bytes):
        encrypted_bytes = base64.b64decode(message.encode())
        decrypted_bytes = await client.ctx.decrypt(encrypted_bytes)
        await next_handler(client, decrypted_bytes)

If the decrypted values are well-formed rfc2812 IRC commands, we can put this handler in front of the default handler
and it will let us use the existing :meth:`Client.trigger<bottom.Client.trigger>` and
:meth:`@Client.on<bottom.Client.on>` methods of registering handlers:

.. code-block:: python

    from bottom import Client

    ctx = EncryptionContext(...)
    client = Client(host=..., port=...)
    client.message_handlers.insert(0, decrypt_message)

    # ping handler is exactly the same - it doesn't have to know the ping was encrypted
    @client.on("ping")
    async def keepalive(message, **kw):
        await client.send("pong", message=message)

Encrypting outgoing messages requires overriding the :meth:`Client.send_message<bottom.Client.send_message>` method:

.. code-block:: python

    import base64
    from bottom import Client

    class EncryptingClient(Client):
        ctx: EncryptionContext

        def __init__(self, ctx: EncryptionContext, *a, **kw):
            super().__init__(*a, **kw)
            self.ctx = ctx

        async def send_message(self, message: str):
            plaintext_bytes = message.encode()
            ciphertext_bytes = await self.ctx.encrypt(plaintext_bytes)
            ciphertext_str = base64.b64encode(ciphertext_bytes).decode()
            await super().send_message(ciphertext_str)

Finally, we can add the decrypt_message handler to our ``EncryptingClient.__init__`` to handle both directions:

.. code-block:: python

    def __init__(self, ctx: EncryptionContext, *a, **kw):
        super().__init__(*a, **kw)
        self.ctx = ctx
        self.message_handlers.insert(0, decrypt_message)


Now any calls to :meth:`Client.send<bottom.Client.send>` will pass through our custom ``send_message`` before they're
sent to the Protocol.
