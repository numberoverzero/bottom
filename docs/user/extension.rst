Extensions
==========

bottom doesn't have any clever import hooks to identify plugins based on name,
shape, or other significant denomination.  Instead, we can create extensions
by using functions or classes that take an instance of the client as an
argument, and hooking up other functions to that client through ``client.on``.


Keepalive
---------

Instead of remembering to respond to ``PING`` in a timely fashion every time we
write a new client, let's write a reusable plugin that we can apply to every
client::

    # my_plugin.py
    def keepalive(client):
        @client.on("ping")
        def handle(message=None, **kwargs):
            message = message or ""
            client.send("pong", message=message)

That's it!  And to use it::

    import bottom
    from my_plugin import keepalive

    client = bottom.Client(...)
    keepalive(client)


Returning new objects
---------------------

Aside from subclassing ``bottom.Client``, we can use a class to expose
additional behavior around a client.  This can be useful in cases where we're
worried about other plugins assigning different meaning to the same attributes
::
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

                # Get the local logger's method by name ex. `self.local.info`
                method = getattr(self.local, level.lower())
                method(message)

        def _on_disconnect(self):
            self.local.warning("Remote logging client disconnected!")


        def debug(self, message):
            self.log("debug", message)

        # Same for info, warning, ...
        ...

And it's usage::

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

Second, we've attached a handler to the client as part of creating the Logger
instance::

    def __init__(self, client, ...):
        ...
        client.on("client_disconnect", self._on_disconnect)
