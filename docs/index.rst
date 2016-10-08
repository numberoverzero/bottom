lightweight asyncio IRC client
==============================

With a very small API, bottom_ lets you wrap an IRC connection and handle
events how you want.  There are no assumptions about reconnecting, rate
limiting, or even when to respond to PINGs.

Explicit is better than implicit: no magic importing or naming to remember for
plugins.  `Extend <user/extension.html>`_ the client with the same ``@on``
decorator.

----

Create an instance:

.. code-block:: python

    import bottom

    host = 'chat.freenode.net'
    port = 6697
    ssl = True

    NICK = "bottom-bot"
    CHANNEL = "#bottom-dev"

    bot = bottom.Client(host=host, port=port, ssl=ssl)


Send nick/user/join when connection is established:

.. code-block:: python

    @bot.on('CLIENT_CONNECT')
    def connect(**kwargs):
        bot.send('NICK', nick=NICK)
        bot.send('USER', user=NICK,
                 realname='https://github.com/numberoverzero/bottom')
        bot.send('JOIN', channel=CHANNEL)


Respond to ping:

.. code-block:: python

    @bot.on('PING')
    def keepalive(message, **kwargs):
        bot.send('PONG', message=message)


Echo messages (channel and direct messages):

.. code-block:: python

    @bot.on('PRIVMSG')
    def message(nick, target, message, **kwargs):
        """ Echo all messages """

        # Don't echo ourselves
        if nick == NICK:
            return
        # Respond directly to direct messages
        if target == NICK:
            bot.send("PRIVMSG", target=nick, message=message)
        # Channel message
        else:
            bot.send("PRIVMSG", target=target, message=message)


Connect and run the bot forever:

.. code-block:: python

    bot.loop.create_task(bot.connect())
    bot.loop.run_forever()


.. toctree::
    :hidden:
    :maxdepth: 2

    user/installation
    user/async
    user/api
    user/events
    user/commands
    user/extension
    dev/development

.. _bottom: https://github.com/numberoverzero/bottom
