.. image:: https://readthedocs.org/projects/bottom-docs/badge?style=flat-square
    :target: http://bottom-docs.readthedocs.org/
.. image:: https://img.shields.io/travis/numberoverzero/bottom/master.svg?style=flat-square
    :target: https://travis-ci.org/numberoverzero/bottom
.. image:: https://img.shields.io/pypi/v/bottom.svg?style=flat-square
    :target: https://pypi.python.org/pypi/bottom
.. image:: https://img.shields.io/github/issues-raw/numberoverzero/bottom.svg?style=flat-square
    :target: https://github.com/numberoverzero/bottom/issues
.. image:: https://img.shields.io/pypi/l/bottom.svg?style=flat-square
    :target: https://github.com/numberoverzero/bottom/blob/master/LICENSE

asyncio-based rfc2812-compliant IRC Client (3.8+)

bottom isn't a kitchen-sink library.  Instead, it provides a consistent API
with a small surface area, tuned for performance and ease of extension.
Similar to the routing style of bottle.py, hooking into events is one line.

Installation
============
::

    pip install bottom

Getting Started
===============

(the full documentation is available here: http://bottom-docs.readthedocs.io/)

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
        # don't echo self
        if nick == NICK: return
        # respond directly
        if target == NICK: target = nick
        bot.send("PRIVMSG", target=target, message=message)


Connect and run the bot forever:

.. code-block:: python

    bot.loop.create_task(bot.connect())
    bot.loop.run_forever()

API
===

The full API consists of 1 class, with 8 methods:

.. code-block:: python

    # manage connections

    async Client.connect()
    async Client.disconnect()

    # send, receive, and wait for rfc-2812 messages

    Client.send(command, **kwargs)
    @Client.on(event)
    Client.trigger(event, **kwargs)
    async Client.wait(event)

    # send and receive anything newline-terminated,
    # provided for eg. IRCv3 extensions

    Client.send_raw(message)
    Client.handle_raw(message)


Contributors
============

* `fahhem <https://github.com/fahhem>`_
* `thebigmunch <https://github.com/thebigmunch>`_
* `tilal6991 <https://github.com/tilal6991>`_
* `AMorporkian <https://github.com/AMorporkian>`_
* `nedbat <https://github.com/nedbat>`_
* `Coinkite Inc <https://github.com/coinkite>`_
* `Johan Lorenzo <https://github.com/JohanLorenzo>`_
* `Dominik Miedziński <https://github.com/miedzinski>`_
* `Yay295 <https://github.com/Yay295>`_
* `Elijah Lazkani <https://github.com/elazkani>`_
