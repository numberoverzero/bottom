.. image:: https://readthedocs.org/projects/bottom/badge?style=flat-square
    :target: http://bottomdocs.readthedocs.io/
.. image:: https://img.shields.io/travis/numberoverzero/bottom/master.svg?style=flat-square
    :target: https://travis-ci.org/numberoverzero/bottom
.. image:: https://img.shields.io/coveralls/numberoverzero/bottom/master.svg?style=flat-square
    :target: https://coveralls.io/github/numberoverzero/bottom
.. image:: https://img.shields.io/pypi/v/bottom.svg?style=flat-square
    :target: https://pypi.python.org/pypi/bottom
.. image:: https://img.shields.io/github/issues-raw/numberoverzero/bottom.svg?style=flat-square
    :target: https://github.com/numberoverzero/bottom/issues
.. image:: https://img.shields.io/pypi/l/bottom.svg?style=flat-square
    :target: https://github.com/numberoverzero/bottom/blob/master/LICENSE

asyncio-based rfc2812-compliant IRC Client (3.5+)

bottom isn't a kitchen-sink library.  Instead, it provides a consistent API
with a small surface area, tuned for performance and ease of extension.
Similar to the routing style of bottle.py, hooking into events is one line.

Installation
============
::

    pip install bottom

Getting Started
===============

Create an instance:

.. code-block:: python

    import asyncio
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
    async def connect(**kwargs):
        bot.send('NICK', nick=NICK)
        bot.send('USER', user=NICK,
                 realname='https://github.com/numberoverzero/bottom')

        # Don't try to join channels until the server has
        # sent the MOTD, or signaled that there's no MOTD.
        done, pending = await asyncio.wait(
            [bot.wait("RPL_ENDOFMOTD"),
             bot.wait("ERR_NOMOTD")],
            loop=bot.loop,
            return_when=asyncio.FIRST_COMPLETED
        )

        # Cancel whichever waiter's event didn't come in.
        for future in pending:
            future.cancel()

        bot.send('JOIN', channel=CHANNEL)


Respond to ping:

.. code-block:: python

    @bot.on('PING')
    def keepalive(message, **kwargs):
        bot.send('PONG', message=message)


Echo messages (channel and direct):

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

API
===

The full API consists of 1 class, with 6 methods:

.. code-block:: python

    async Client.connect()

    async Client.disconnect()

    Client.send(command, **kwargs)

    @Client.on(event)

    async Client.wait(event)

    Client.trigger(event, **kwargs)

`Visit the docs`__ for more details and examples.

__ http://bottomdocs.readthedocs.org/user/api.html

Contributors
============

* `fahhem <https://github.com/fahhem>`_
* `thebigmunch <https://github.com/thebigmunch>`_
* `tilal6991 <https://github.com/tilal6991>`_
* `AMorporkian <https://github.com/AMorporkian>`_
* `nedbat <https://github.com/nedbat>`_
* `Coinkite Inc <https://github.com/coinkite>`_
