API
^^^

``Client.on``
=============

.. code-block:: python

    client.on(event)(func)

This decorator is the main way you'll interact with a ``Client``.  For a given
event name, it registers the decorated function to be invoked when that event
occurs.  Your decorated functions should always accept ``**kwargs``, in case
unexpected kwargs are included when the event is triggered.

The usual IRC commands sent from a server are triggered automatically, or can
be manually invoked with ``trigger``.  You may register handlers for any string,
making it easy to extend bottom with your own signals.


Not all available arguments need to be used.  Both of the following are valid:

.. code-block:: python

    @bot.on('PRIVMSG')
    def event(nick, message, target, **kwargs):
        """ Doesn't use user, host.  argument order is different """
        # message sent to bot - echo message
        if target == bot.nick:
            bot.send('PRIVMSG', target, message=message)
        # Some channel we're watching
        elif target == bot.monitored_channel:
            logger.info("{} -> {}: {}".format(nick, target, message))


    @bot.on('PRIVMSG')
    def func(message, target, **kwargs):
        """ Just waiting for the signal """
        if message == codeword && target == secret_channel:
            execute_heist()

Handlers do not need to be async functions - non async will be wrapped prior to
the bot running.  For example, both of these are valid:

.. code-block:: python

    @bot.on('PRIVMSG')
    def handle(message, **kwargs):
        print(message)

    @bot.on('PRIVMSG')
    async def handle(message, **kwargs):
        await async_logger.log(message)

Finally, you can create your own events to trigger and handle.  For example,
let's catch SIGINT and gracefully shut down the event loop:

.. code-block:: python

    import signal

    def handle_sigint(signum, frame):
        print("SIGINT handler")
        bot.trigger("my.sigint.event")
    signal.signal(signal.SIGINT, handle_sigint)


    @bot.on("my.sigint.event")
    async def handle(**kwargs):
        print("SIGINT trigger")
        await bot.disconnect()

        # Signal a stop before disconnecting so that any reconnect
        # coros aren't run by the last run_forever sweep.
        bot.loop.stop()


    bot.loop.create_task(bot.connect())
    bot.loop.run_forever()  # Ctrl + C here


``Client.trigger``
==================

.. code-block:: python

    client.trigger(event, **kwargs)

Manually inject a command or reply as if it came from the server.  This is
useful for invoking other handlers. Because ``trigger`` doesn't block, registered
callbacks for the event won't run until the event loop yields to them.

Events don't need to be valid irc commands; any string is available.

.. code-block:: python

    # Manually trigger `PRIVMSG` handlers:
    bot.trigger('privmsg', nick="always_says_no", message="yes")

.. code-block:: python

    # Rename !commands to !help
    @bot.on('privmsg')
    def parse(nick, target, message, **kwargs):
        if message == '!commands':
            bot.send('privmsg', target=nick,
                     message="!commands was renamed to !help in 1.2")
            # Don't make them retype it, trigger the correct command
            bot.trigger('privmsg', nick=nick,
                        target=target, message="!help")


Because the ``@on`` decorator returns the original function, you can register
a handler for multiple events.  It's especially important to use ``**kwargs``
correctly here, to handle different keywords for each event.

.. code-block:: python

    # Simple recursive-style countdown
    @bot.on('privmsg')
    @bot.on('countdown')
    async def handle(target, message, remaining=None, **kwargs):
        # Entry point, verify command and parse from message
        if remaining is None:
            if not message.startswith("!countdown"):
                return
            # !countdown 10
            remaining = int(message.split(" ")[-1])

        if remaining == 0:
            message = "Countdown complete!"
        else:
            message = "{}...".format(remaining)
        # Assume for now that target is always a channel
        bot.send("privmsg", target=target, message=message)

        if remaining:
            # After a second trigger another countdown event
            await asyncio.sleep(1, loop=bot.loop)
            bot.trigger('countdown', target=target,
                        message=message, remaining=remaining - 1)


``Client.wait``
===============

.. code-block:: python

    await client.wait(event)

Wait for an event to trigger:

.. code-block:: python

    @bot.on("client_disconnect")
    async def reconnect(**kwargs):
        # Trigger an event that may cascade to a client_connect.
        # Don't continue until a client_connect occurs,
        # which may be never.

        bot.trigger("some.plugin.connection.lost")

        await client.wait("client_connect")

        # If we get here, one of the plugins handled connection lost by
        # reconnecting, and we're back.  Send some messages, etc.
        client.send("privmsg", target=bot.CHANNEL,
                    message="Happy Birthday!")


``Client.connect``
==================

.. code-block:: python

    await client.connect()

Connect to the client's host, port.

.. code-block:: python

    @bot.on('client_disconnect')
    async def reconnect(**kwargs):
        # Wait a few seconds
        await asyncio.sleep(3, loop=bot.loop)
        await bot.connect()
        # Now that we're connected, let everyone know
        bot.send('privmsg', target=bot.channel, message="I'm back.")


You can schedule a non-blocking connect with the client's event loop:

.. code-block:: python

    @bot.on('client_disconnect')
    def reconnect(**kwargs):
        # Wait a few seconds

        # Note that we're not in a coroutine, so we don't have access
        # to await and asyncio.sleep
        time.sleep(3)

        # After this line we won't necessarily be connected.
        # We've simply scheduled the connect to happen in the future
        bot.loop.create_task(bot.connect())

        print("Reconnect scheduled.")

``Client.disconnect``
=====================

.. code-block:: python

    await client.disconnect()

Immediately disconnect from the server.

.. code-block:: python

    @bot.on('privmsg')
    async def disconnect_bot(nick, message, **kwargs):
        if nick == "myNick" and message == "disconnect:hunter2":
            await bot.disconnect()
            logger.log("disconnected bot.")


Like ``connect``, use the bot's event loop to schedule a disconnect:

.. code-block:: python

    bot.loop.create_task(bot.disconnect())


``Client.send``
===============

.. code-block:: python

    client.send(command, **kwargs)

Send a command to the server.  See `Commands <user/commands.html>`_.


``Client.handle_raw``
=====================

.. versionadded:: 2.1.0

.. code-block:: python

    client.handle_raw(message)

Manually inject a raw command.  The client's ``raw_handlers`` will process
the message.  By default, every ``Client`` is configured with a ``rfc2812_handler``
which unpacks a conforming rfc 2812 message into an event and calls ``client.trigger``.

You can disable this functionality by removing the handler:

.. code-block:: python

    client = Client(host="localhost", port=443)
    client.raw_handlers.clear()


``Client.send_raw``
===================

.. versionadded:: 2.1.0

.. code-block:: python

    client.send_raw(message)

Send a complete IRC line without the Client reconstructing or modifying the message.
To easily send an rfc 2812 message, you should instead consider ``Client.send``.
