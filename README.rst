bottom 0.9.0
============

:Build: |build|_ |coverage|_
:Downloads: http://pypi.python.org/pypi/bottom
:Source: https://github.com/numberoverzero/bottom

.. |build| image:: https://travis-ci.org/numberoverzero/bottom.svg?branch=master
.. _build: https://travis-ci.org/numberoverzero/bottom
.. |coverage| image:: https://coveralls.io/repos/numberoverzero/bottom/badge.png?branch=master
.. _coverage: https://coveralls.io/r/numberoverzero/bottom?branch=master

asyncio-based rfc2812-compliant IRC Client

Installation
============

``pip install bottom``

Getting Started
===============

bottom isn't a kitchen-sink library.  Instead, it provides an API with a small
surface area, tuned for performance and ease of extension.  Similar to the
routing style of bottle.py, hooking into events is one line.

::

    from bottom import Client

    NICK = 'bottom-bot'
    CHANNEL = '#python'

    bot = Client('localhost', 6697)


    @bot.on('CLIENT_CONNECT')
    def connect():
        bot.send('NICK', NICK)
        bot.send('USER', NICK, 0, '*', message='Bot using bottom.py')
        bot.send('JOIN', CHANNEL)


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
            bot.send("PRIVMSG", nick, message=message)
        # Message in channel
        else:
            bot.send("PRIVMSG", target, message=message)

    bot.run()

API
===

While there are other internal classes and structures, everything should be
considered private except the `Client` class.

Client.run
----------

Client.on
----------

Client.connect
--------------

Client.disconnect
-----------------

Client.send
-----------

Other Classes and Modules
-------------------------

The `routing` module is used to unpack an irc line into the appropriate named
objects based on the command's grammar.

The `rfc` module holds a set of command aliases and the full list of rfc2812's
available command and response strings.  It primarily parses a single line of
text into a (prefix, command, params, message) tuple which is (usually)
consumed by the router.  It also handles dumping a command into the appropriate
wire format.

The `Connection` class handles the main read/write loop and socket connections,
and is entirely asynchronous.

The `Handler` class is used to distribute events and register functions
decorated by `Client.on`.  It does some optimization using the `partial_bind`
function to speed up the connection read -> function call time.

Supported Commands
==================

All commands and responses listed in http://tools.ietf.org/html/rfc2812
will be available.  Currently, only the following have working parsers:

* PING
* CLIENT_CONNECT
* CLIENT_DISCONNECT
* NOTICE
* PRIVMSG
* JOIN
* PART
* QUIT
* RPL_MOTDSTART
* RPL_MOTD
* RPL_ENDOFMOTD
* RPL_WELCOME
* RPL_YOURHOST
* RPL_CREATED,
* RPL_LUSERCLIENT
* RPL_LUSERME
* RPL_STATSDLINE
* RPL_LUSEROP
* RPL_LUSERUNKNOWN
* RPL_LUSERCHANNELS
* RPL_MYINFO
* RPL_BOUNCE

Command Parameters
==================

This section will eventually list the available parameters for each command or
reply, and what type they are.
