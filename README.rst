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

Downloads https://pypi.python.org/pypi/bottom

Source https://github.com/numberoverzero/bottom

asyncio-based rfc2812-compliant IRC Client

Installation
============
::

    pip install bottom

Getting Started
===============

bottom isn't a kitchen-sink library.  Instead, it provides a consistent API with a small surface area, tuned for performance and ease of extension.  Similar to the routing style of bottle.py, hooking into events is one line.

::

    import bottom
    import asyncio

    NICK = 'bottom-bot'
    CHANNEL = '#python'

    bot = bottom.Client('localhost', 6697)


    @bot.on('CLIENT_CONNECT')
    def connect():
        bot.send('NICK', nick=NICK)
        bot.send('USER', user=NICK, realname='Bot using bottom.py')
        bot.send('JOIN', channel=CHANNEL)


    @bot.on('PING')
    def keepalive(message):
        bot.send('PONG', message=message)


    @bot.on('PRIVMSG')
    def message(nick, target, message):
        ''' Echo all messages '''

        # Don't echo ourselves
        if nick == NICK:
            return
        # Direct message to bot
        if target == NICK:
            bot.send("PRIVMSG", target=nick, message=message)
        # Message in channel
        else:
            bot.send("PRIVMSG", target=target, message=message)

    asyncio.get_event_loop().run_until_complete(bot.run())

Versioning  and RFC2812
=======================

* Bottom follows semver for its **public** API.

  * Currently, ``Client`` is the only public member of bottom.
  * IRC replies/codes which are not yet implemented may be added at any time, and will correspond to a patch - the function contract of ``@on`` method does not change.
  * You should not rely on the internal api staying the same between minor versions.
  * Over time, private apis may be raised to become public.  The reverse will never occur.

* There are a number of changes from RFC2812 - none should noticeably change how you interact with a standard IRC server.  For specific adjustments, see the notes section of each command in supported_commands_.

Contributing
============

Contributions welcome!  When reporting issues, please provide enough detail to reproduce the bug - sample code is ideal.  When submitting a PR, please make sure ``tox`` passes (including flake8).

Development
-----------

bottom uses ``tox``, ``pytest`` and ``flake8``.  To get everything set up::

    # RECOMMENDED: create a virtualenv with:
    #     mkvirtualenv bottom
    git clone https://github.com/numberoverzero/bottom.git
    pip install tox
    tox


TODO
----

* Better `Client` docstrings
* Add missing replies/errors to `unpack.py:unpack_command`
  * Add reply/error parameters to `unpack.py:parameters`
  * Document [`Supported Events`](#supported-events)


Contributors
------------
* [fahhem](https://github.com/fahhem)
* [thebigmunch](https://github.com/thebigmunch)
* [tilal6991](https://github.com/tilal6991)

API
===

Client.run()
------------

*This is a coroutine.*

Start the magic.  This will connect the client, and then read until it disconnects.  The ``CLIENT_DISCONNECT`` event will fire before the loop exits, allowing you to ``yield from Client.connect()`` and keep the client running.

If you want to call this synchronously (block until it's complete) use the following::

    import asyncio
    # ... client is defined somewhere

    loop = asyncio.get_event_loop()
    task = client.run()
    loop.run_until_complete(task)


Client.on(event)(func)
----------------------

This ``@decorator`` is the main way you'll interact with a ``Client``.  It takes a string, returning a function wrapper that validates the function and registers it for the given event.  When that event occurs, the function will be called, mapping any arguments the function may expect from the set of available arguments for the event.

Not all available arguments need to be used.  For instance, both of the following are valid::

    @bot.on('PRIVMSG')
    def event(nick, message, target):
        ''' Doesn't use user, host.  argument order is different '''
        # message sent to bot - echo message
        if target == bot.nick:
            bot.send('PRIVMSG', target, message=message)
        # Some channel we're watching
        elif target == bot.monitored_channel:
            logger.info("{} -> {}: {}".format(nick, target, message))


    @bot.on('PRIVMSG')
    def func(message, target):
        ''' Just waiting for the signal '''
        if message == codeword && target == secret_channel:
            execute_heist()


VAR_KWARGS can be used, as long as the name doesn't mask an actual parameter.  VAR_ARGS may not be used.

::

    # OK - kwargs, no masking
    @bot.on('PRIVMSG')
    def event(message, **everything_else):
        logger.log(everything_else['nick'] + " said " + message)


    # NOT OK - kwargs, masking parameter <nick>
    @bot.on('PRIVMSG')
    def event(message, **nick):
        logger.log(nick['target'])


    # NOT OK - uses VAR_ARGS
    @bot.on('PRIVMSG')
    def event(message, *args):
        logger.log(args)


Decorated functions will be invoked asynchronously, and may optionally use the ``yield from`` syntax.  Functions do not need to be wrapped with ``@ayncio.coroutine`` - this is handled as part of the function caching process.

Client.trigger(event, **kwargs)
-------------------------------

*This is a coroutine.*

Manually inject a command or reply as if it came from the server.  This is useful for invoking other handlers.

::

    # Manually trigger `PRIVMSG` handlers:
    yield from bot.trigger('privmsg', nick="always_says_no", message="yes")

::

    # Rename !commands to !help
    @bot.on('privmsg')
    def parse(nick, target, message):
        if message == '!commands':
            bot.send('privmsg', target=nick,
                     message="!commands was renamed to !help in 1.2")
            # Don't make them retype it, just make it happen
            yield from bot.trigger('privmsg', nick=nick,
                                   target=target, message="!help")

::

    # While testing the auto-reconnect module, simulate a disconnect:
    def test_reconnect(bot):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(bot.trigger("client_disconnect"))
        assert bot.connected

Client.connect()
----------------

*This is a coroutine.*

Attempt to reconnect using the client's host, port::

    @bot.on('client_disconnect')
    def reconnect():
        # Wait a few seconds
        yield from asyncio.sleep(3)
        yield from bot.connect()


Client.disconnect()
-------------------

*This is a coroutine.*

Disconnect from the server if connected::

    @bot.on('privmsg')
    def suicide_pill(nick, message):
        if nick == "spy_handler" and message == "last stop":
            yield from bot.disconnect()

Client.send(command, **kwargs)
------------------------------

Send a command to the server.  See supported_commands_ for a detailed breakdown of available commands and their parameters.

.. _supported_commands:

Supported Commands
==================

These commands can be sent to the server using ``Client.send``.

For incoming signals and messages, see supported_events_ below.

::

    # Local only events
    client.trigger('CLIENT_CONNECT', host='localhost', port=6697)
    client.trigger('CLIENT_DISCONNECT', host='localhost', port=6697)

::

    client.send('PASS', password='hunter2')

::

    client.send('NICK', nick='WiZ')

::

    # mode is optional, default is 0
    client.send('USER', user='WiZ-user', realname='Ronnie')
    client.send('USER', user='WiZ-user', mode='8', realname='Ronnie')

::

    client.send('OPER', user='WiZ', password='hunter2')

::

    # Renamed from MODE
    client.send('USERMODE', nick='WiZ')
    client.send('USERMODE', nick='WiZ', modes='+io')

::

    client.send('SERVICE', nick='CHANSERV', distribution='*.en',
                type='0', info='manages channels')

::

    client.send('QUIT')
    client.send('QUIT', message='Gone to Lunch')

::

    client.send('SQUIT', server='tolsun.oulu.fi')
    client.send('SQUIT', server='tolsun.oulu.fi', message='Bad Link')

::

    # If channel has n > 1 values, key MUST have 1 or n values
    client.send('JOIN', channel='0')  # send PART to all joined channels
    client.send('JOIN', channel='#foo-chan')
    client.send('JOIN', channel='#foo-chan', key='foo-key')
    client.send('JOIN', channel=['#foo-chan', '#other'], key='key-for-both')
    client.send('JOIN', channel=['#foo-chan', '#other'], key=['foo-key', 'other-key'])

::

    client.send('PART', channel='#foo-chan')
    client.send('PART', channel=['#foo-chan', '#other'])
    client.send('PART', channel='#foo-chan', message='I lost')

::

    # Renamed from MODE
    client.send('CHANNELMODE', channel='#foo-chan', modes='+b')
    client.send('CHANNELMODE', channel='#foo-chan', modes='+l', params='10')

::

    client.send('TOPIC', channel='#foo-chan')
    client.send('TOPIC', channel='#foo-chan', message='')  # Clear channel message
    client.send('TOPIC', channel='#foo-chan', message='Yes, this is dog')

::

    # target requires channel
    client.send('NAMES')
    client.send('NAMES', channel='#foo-chan')
    client.send('NAMES', channel=['#foo-chan', '#other'])
    client.send('NAMES', channel=['#foo-chan', '#other'], target='remote.*.edu')

::

    # target requires channel
    client.send('LIST')
    client.send('LIST', channel='#foo-chan')
    client.send('LIST', channel=['#foo-chan', '#other'])
    client.send('LIST', channel=['#foo-chan', '#other'], target='remote.*.edu')

::

    client.send('INVITE', nick='WiZ-friend', channel='#bar-chan')

::

    # nick and channel must have the same number of elements
    client.send('KICK', channel='#foo-chan', nick='WiZ')
    client.send('KICK', channel='#foo-chan', nick='WiZ', message='Spamming')
    client.send('KICK', channel='#foo-chan', nick=['WiZ', 'WiZ-friend'])
    client.send('KICK', channel=['#foo', '#bar'], nick=['WiZ', 'WiZ-friend'])

::

    client.send('PRIVMSG', target='WiZ-friend', message='Hello, friend!')

::

    client.send('NOTICE', target='#foo-chan', message='Maintenance in 5 mins')

::

    client.send('MOTD')
    client.send('MOTD', target='remote.*.edu')

::

    client.send('LUSERS')
    client.send('LUSERS', mask='*.edu')
    client.send('LUSERS', mask='*.edu', target='remote.*.edu')

::

    client.send('VERSION')

::

    # target requires query
    client.send('STATS')
    client.send('STATS', query='m')
    client.send('STATS', query='m', target='remote.*.edu')

::

    # remote requires mask
    client.send('LINKS')
    client.send('LINKS', mask='*.bu.edu')
    client.send('LINKS', remote='*.edu', mask='*.bu.edu')

::

    client.send('TIME')
    client.send('TIME', target='remote.*.edu')

::

    client.send('CONNECT', target='tolsun.oulu.fi', port=6667)
    client.send('CONNECT', target='tolsun.oulu.fi', port=6667, remote='*.edu')

::

    client.send('TRACE')
    client.send('TRACE', target='remote.*.edu')

::

    client.send('ADMIN')
    client.send('ADMIN', target='remote.*.edu')

::

    client.send('INFO')
    client.send('INFO', target='remote.*.edu')

::

    # type requires mask
    client.send('SERVLIST', mask='*SERV')
    client.send('SERVLIST', mask='*SERV', type=3)

::

    client.send('SQUERY', target='irchelp', message='HELP privmsg')

::

    client.send('WHO')
    client.send('WHO', mask='*.fi')
    client.send('WHO', mask='*.fi', o=True)

::

    client.send('WHOIS', mask='*.fi')
    client.send('WHOIS', mask=['*.fi', '*.edu'], target='remote.*.edu')

::

    # target requires count
    client.send('WHOWAS', nick='WiZ')
    client.send('WHOWAS', nick='WiZ', count=10)
    client.send('WHOWAS', nick=['WiZ', 'WiZ-friend'], count=10)
    client.send('WHOWAS', nick='WiZ', count=10, target='remote.*.edu')

::

    client.send('KILL', nick='WiZ', message='Spamming Joins')

::

    # server2 requires server1
    client.send('PING', message='Test..')
    client.send('PING', server2='tolsun.oulu.fi')
    client.send('PING', server1='WiZ', server2='tolsun.oulu.fi')

::

    # server2 requires server1
    client.send('PONG', message='Test..')
    client.send('PONG', server2='tolsun.oulu.fi')
    client.send('PONG', server1='WiZ', server2='tolsun.oulu.fi')

::

    client.send('AWAY')
    client.send('AWAY', message='Gone to Lunch')

::

    client.send('REHASH')

::

    client.send('DIE')

::

    client.send('RESTART')

::

    # target requires channel
    client.send('SUMMON', nick='WiZ')
    client.send('SUMMON', nick='WiZ', target='remote.*.edu')
    client.send('SUMMON', nick='WiZ', target='remote.*.edu', channel='#foo-chan')

::

    client.send('USERS')
    client.send('USERS', target='remote.*.edu')

::

    client.send('WALLOPS', message='Maintenance in 5 minutes')

::

    client.send('USERHOST', nick='WiZ')
    client.send('USERHOST', nick=['WiZ', 'WiZ-friend'])

::

    client.send('ISON', nick='WiZ')
    client.send('ISON', nick=['WiZ', 'WiZ-friend'])

.. _supported_events:

Supported Events
================

These commands are received from the server, or dispatched using ``Client.trigger(...)``.

For sending commands, see supported_commands_ above.

* PING
* JOIN
* PART
* PRIVMSG
* NOTICE
* RPL_WELCOME (001)
* RPL_YOURHOST (002)
* RPL_CREATED (003)
* RPL_MYINFO (004)
* RPL_BOUNCE (005)
* RPL_MOTDSTART (375)
* RPL_MOTD (372)
* RPL_ENDOFMOTD (376)
* RPL_LUSERCLIENT (251)
* RPL_LUSERME (255)
* RPL_LUSEROP (252)
* RPL_LUSERUNKNOWN (253)
* RPL_LUSERCHANNELS (254)
