.. _Extensions:

Extending the Client
^^^^^^^^^^^^^^^^^^^^

bottom doesn't have any clever import hooks to identify plugins based on name, shape, or other significant
denomination.  Instead, we can create extensions by using :meth:`Client.on<bottom.Client.on>`.

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

*(The full source for extension is available at examples/registry.py)*

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


Pattern matching
================

*(The full source for extension is available at examples/regex.py)*

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

*(The full source for extension is available at examples/encryption.py)*

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
