Extensions
==========

bottom doesn't have any clever import hooks to identify plugins based on name,
shape, or other significant denomination.  Instead, we can create extensions
by using ``client.on`` on a ``Client`` instance.

Keepalive
---------

Instead of writing the same ``PING`` handler everywhere, a reusable plugin:

.. code-block:: python

    # my_plugin.py
    def keepalive(client):
        @client.on("ping")
        def handle(message=None, **kwargs):
            message = message or ""
            client.send("pong", message=message)

That's it!  And to use it:

.. code-block:: python

    import bottom
    from my_plugin import keepalive

    client = bottom.Client(...)
    keepalive(client)


Returning new objects
---------------------

Aside from subclassing ``bottom.Client``, we can use a class to expose
additional behavior around a client.  This can be useful when we're worried
about other plugins assigning different meaning to the same attributes:

.. code-block:: python

    # irc_logging.py
    class Logger:
        def __init__(self, client, local_logger):
            self.client = client
            self.local = local_logger
            client.on("client_disconnect", self._on_disconnect)

        def log(self, level, message):
            try:
                self.client.send("{}: {}".format(level.upper(), message))
            catch RuntimeError:
                self.local.warning("Failed to log to remote")

                # Get the local logger's method by name
                # ex. `self.local.info`
                method = getattr(self.local, level.lower())
                method(message)

        def _on_disconnect(self):
            self.local.warning("Remote logging client disconnected!")


        def debug(self, message):
            self.log("debug", message)

        # Same for info, warning, ...
        ...

And its usage:

.. code-block:: python

    import bottom
    import logging
    from irc_logging import Logger

    local_logger = logging.getLogger(__name__)

    client = bottom.Client(...)
    remote_logger = Logger(client, local_logger)


    @client.on("client_connect")
    def log_connect(**kwargs):
        remote_logger.info("Connected!")

    # Connect and send "INFO: Connected!"
    client.loop.run_until_complete(client.connect())

Notice that the logging functionality is part of a different object, not the
client.  This keeps the namespace clean, and reduces the attribute contention
that can occur when multiple plugins store their information directly on the
client instance.

This line hooked the logger's disconnect handler to the client:

.. code-block:: python

    def __init__(self, client, ...):
        ...
        client.on("client_disconnect", self._on_disconnect)


Pattern matching
----------------

We can write a simple wrapper class to annotate functions to handle PRIVMSG matching a regex.
To keep the interface simple, we can use bottom's annotation pattern and pass the regex to match.

In the following example, we'll define a handler that echos whatever a user asks for, if it's in the correct format:

.. code-block:: python


    import bottom

    client = bottom.Client(host=host, port=port, ssl=ssl)
    router = Router(client)


    @router.route("^bot, say (\w+)\.$")
    def echo(self, nick, target, message, match, **kwargs):
        if target == router.nick:
            # respond in a direct message
            target = nick
        client.send("privmsg", target=target, message=match.group(1))


Now, the Router class needs to manage the regex -> handler mapping and connect an event handler to PRIVMSG on its
client:


.. code-block:: python

    import asyncio
    import functools
    import re


    class Router(object):
        def __init__(self, client):
            self.client = client
            self.routes = {}
            client.on("PRIVMSG")(self._handle)

        def _handle(self, nick, target, message, **kwargs):
            """ client callback entrance """
            for regex, (func, pattern) in self.routes.items():
                match = regex.match(message)
                if match:
                    self.client.loop.create_task(func(nick, target, message, match, **kwargs))

        def route(self, pattern, func=None, **kwargs):
            if func is None:
                return functools.partial(self.route, pattern)

            # Decorator should always return the original function
            wrapped = func
            if not asyncio.iscoroutinefunction(wrapped):
                wrapped = asyncio.coroutine(wrapped)

            compiled = re.compile(pattern)
            self.routes[compiled] = (wrapped, pattern)
            return func


Wait for any events
-------------------

Use :func:`Client.wait` to pause until one or all signals have fired.  For example, after sending NICK/USER during
CLIENT_CONNECT, some servers will ignore subsequent commands until they have finished sending RPL_ENDOFMOTD.  This
can be used to wait for any signal that the MOTD has been sent (eg. ERR_NOMOTD may be sent instead of RPL_ENDOFMOTD).

.. code-block:: python

    import asyncio


    def waiter(client):
        async def wait_for(*events, return_when=asyncio.FIRST_COMPLETED):
            if not events:
                return
            done, pending = await asyncio.wait(
                [bot.wait(event) for event in events],
                loop=bot.loop,
                return_when=return_when)

            # Cancel any events that didn't come in.
            for future in pending:
                future.cancel()
        return wait_for

To use in the CLIENT_CONNECT process:

.. code-block:: python

    import bottom
    client = bottom.Client(...)
    wait_for = waiter(client)


    @client.on("CLIENT_CONNECT")
    async def on_connect(**kwargs):
        client.send('nick', ...)
        client.send('user', ...)

        await wait_for('RPL_ENDOFMOTD', 'ERR_NOMOTD')

        client.send('join', ...)

Send and trigger raw messages
-----------------------------

.. versionadded:: 2.1.0

Extensions do not need to strictly conform to rfc 2812.
You can send or trigger custom messages with ``Client.send_raw`` and
``Client.handle_raw``.  For example, the following can be used to request
Twitch.tv's `Membership capability`__ using IRC v3's capabilities registration:

.. code-block:: python

    client = MyTwitchClient(...)
    client.send_raw("CAP REQ :twitch.tv/membership")

Just as ``Client.trigger`` can be used to manually invoke handlers for a specific
event, ``Client.handle_raw`` can be called to manually invoke raw handlers for a
given message.  For the above example, you can ensure you handle the response from
Twitch.tv with the following:

.. code-block:: python

    response = ":tmi.twitch.tv CAP * ACK :twitch.tv/membership"
    client = MyTwitchClient(...)
    client.handle_raw(response)


__ https://dev.twitch.tv/docs/v5/guides/irc#twitch-specific-irc-capabilities


Raw handlers
------------

.. versionadded:: 2.1.0

Clients can extend or replace the default message handler by
modifying the ``Client.raw_handlers`` list.  This is a list of async
functions that take a ``(next_handler, message)`` tuple.  To allow
the next handler to process a message, call ``next_handler(message)``
within your handler.  You may also send a different message to the subsequent
handler, or not invoke it at all.

The following listens for responses from twitch.tv about capabilities and
logs them.  Otherwise, it passes the message on to the next handler.

.. code-block:: python

    import re
    CAPABILITY_RESPONSE_PATTERN = re.compile(
        "^:tmi\.twitch\.tv CAP \* ACK :twitch\.tv/\w+$")


    async def capability_handler(next_handler, message):
        if CAPABILITY_RESPONSE_PATTERN.match(message):
            print("Capability granted: " + message)
        else:
            await next_handler(message)


And to ensure it runs before the default handler:

.. code-block:: python

    client = Client(...)
    client.raw_handlers.insert(0, capability_handler)

Unlike ``Client.on``, raw handlers must be async functions.


Handlers may send a different message than they receive.  The following
can be used to forward messages from one chat room to another:

.. code-block:: python

    from bottom.pack import pack_command
    from bottom.unpack import unpack_command


    def forward(old_room, new_room):
        async def handle(next_handler, message):
            try:
                event, kwargs = unpack_command(message)
            except ValueError:
                # pass message unchanged
                pass
            else:
                if event.lower() == "privmsg":
                    if kwargs["target"].lower() == old_room.lower():
                        kwargs["target"] = new_room
                        message = pack_command("privmsg", **kwargs)
            await next_handler(message)
        return handle

And its usage:


.. code-block:: python

    client = Client(...)

    forwarding = forward("bottom-legacy", "bottom-dev")
    client.raw_handlers.insert(0, forwarding)

Full message encryption
-----------------------

This is a more complex example of a raw handler where messages are encrypted
and then base64 encoded.  On the wire their only similarity with the IRC protocol
is a newline terminating character.  This is enough to build an extension to
transparently encrypt data.

Assume you have implemented a class with the following interface:

.. code-block:: python

    class EncryptionContext:
        def encrypt(self, data: bytes) -> bytes:
            ...

        def decrypt(self, data: bytes) -> bytes:
            ...

the following extension can be written:

.. code-block:: python

    import base64

    def encryption_handler(context: EncryptionContext):
        async def handle_decrypt(next_handler, message):
            message = context.decrypt(
                base64.b64decode(
                    message.encode("utf-8")
                )
            ).decode("utf-8")
            await next_handler(message)
        return handle_decrypt

to encrypt messages as they are sent, the class can override
``Client.send_raw``.  Adding in the encryption handler above:


.. code-block:: python

    class EncryptedClient(Client):
        def __init__(self, encryption_context, **kwargs):
            super().__init__(**kwargs)
            self.raw_handlers.append(
                encryption_handler(encryption_context))
            self.context = encryption_context

        def send_raw(self, message: str) -> None:
            message = base64.b64encode(
                self.context.encrypt(
                    message.encode("utf-8")
                )
            ).decode("utf-8")
            super().send_raw(message)
