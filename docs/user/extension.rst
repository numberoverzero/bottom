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
