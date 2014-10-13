bottom
========
:Build: |build|_ |coverage|_
:Downloads: http://pypi.python.org/pypi/bottom
:Source: https://github.com/numberoverzero/bottom

.. |build| image:: https://travis-ci.org/numberoverzero/bottom.svg?branch=master
.. _build: https://travis-ci.org/numberoverzero/bottom
.. |coverage| image:: https://coveralls.io/repos/numberoverzero/bottom/badge.png?branch=master
.. _coverage: https://coveralls.io/r/numberoverzero/bottom?branch=master

bottom layer of the irc protocol for python's asyncio

Installation
============

``pip install bottom``

Getting Started
===============
::

    from bottom import Client

    NICK = 'bottom-bot'
    channel = '#python'

    bot = Client('localhost', 6697)


    @bot.on('CLIENT_CONNECT')
    def connect():
        bot.send('NICK', NICK)
        bot.send('USER', NICK, 0, '*', message="Bot using bottom.py")
        bot.send('JOIN', channel)


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

Client API
============

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
* RPL_LUSEROP
* RPL_LUSERUNKNOWN
* RPL_LUSERCHANNELS
* RPL_MYINFO
* RPL_BOUNCE
* RPL_WELCOME
* RPL_YOURHOST
* RPL_CREATED
* RPL_LUSERCLIENT
* RPL_LUSERME
* RPL_STATSDLINE
