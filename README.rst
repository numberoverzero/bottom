bottom
========
:Build: |build|_ |coverage|_
:Documentation: http://bottom.readthedocs.org/
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
    nick = 'bottom-bot'
    channel = '#python'
    bot = Client('localhost', 6697)
    bot.nick = 'bottom-bot'

    @bot.on('CLIENT_CONNECT')
    def connect():
        bot.send('NICK', bot.nick)
        bot.send('USER', bot.nick, 0, '*', message="Bot using bottom.py")
        bot.send('JOIN', channel)


    @bot.on('PING')
    def keepalive(message):
        bot.send('PONG', message=message)


    @bot.on('PRIVMSG')
    def message(nick, target, message):
        ''' Echo messages read '''
        # Don't echo ourselves
        if nick == bot.nick:
            return
        # Direct message to bot
        if target == bot.nick:
            bot.send("PRIVMSG", nick, message=message)
        # Message in channel
        else:
            bot.send("PRIVMSG", target, message=message)

    bot.run()
