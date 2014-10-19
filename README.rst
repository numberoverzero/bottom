bottom 0.9.1
============

:Build: |build|_ |coverage|_
:Downloads: s://pypi.python.org/pypi/bottom
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

    bot.run()

API
===

Versioning
----------

* Bottom follows semver for its **public** API.

  * Currently, ``Client`` is the only public member of bottom.
  * IRC replies/codes which are not yet implemented may be added at any time,
    and will correspond to a patch.  The contract of the ``@on`` method
    does not change - this is only an expansion of legal inputs.

* There are a number of unsupported parameters for IRC commands defined in
  rfc2812 which should be added.  The list of all adjustments can be found in
  ``bottom/pack.py`` in the notes of ``pack_command``.  Any changes listed
  below will be made before 1.0.0, if they occur at all.

  * RENAMES are unlikely to change by 1.0.0.
  * MODE is split into USERMODE and CHANNELMODE and will not change.
  * Any command that doesn't use the ``<target>`` parameter will be updated to
    use it by 1.0.0
  * WHO may get a boolean 'o' parameter
  * PING may be implemented
  * PONG may use ``server1`` and ``server2``
  * PONG will continue to have ``message`` although not defined in rfc2812.
  * ERROR may be implemented

* All private methods are subject to change at any time, and will correspond
  to a patch.

  * You should not rely on the api of any internal methods staying the same
    between minor versions.

* Over time, private apis may be raised to become public.  The reverse will
  never occur.

Client.run
----------

*This is a coroutine.*

Start the magic.  This will connect the client, and then read until it
disconnects.  The ``CLIENT_DISCONNECT`` event will fire before the loop exits,
allowing you to ``yield from Client.connect()`` and keep the client running.

Pseudocode::

    while connected:
        str = read()
        command, dict = parse(str)
        on(command, **dict)
        if not connected:
            on('client_disconnect', ...)

Client.on
----------

This ``@decorator`` is the main way you'll interact with a ``Client``.  It
takes a string, returning a function wrapper that validates the function and
registers it for the given event.  When that event occurs, the function will be
called, mapping any arguments the function may expect from the set of available
arguments for the event.

For example, ``PRIVMSG`` has the following arguments::

    nick - nickname of the sender
    user - user of the sender
    host - host of the sender
    target - channel or user the message was sent to
    message - message sent

Both of these are perfectly valid::

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

Note that VAR_ARGS and VAR_KWARGS are both unavailable, so the following would
throw::

    @bot.on('PRIVMSG')
    def event(message, **everything_else):
        logger.log(everything_else['nick'] + " said " + message)

There is some magic in the mapping of arguments, but it should begin to feel
familiar with just a bit of usage.  If you try to use an argument that's not
available for an event, an exception will be thrown.  There's also the handy
(but incomplete) reference below of each event and the available arguments.

Functions will be invoked asynchronously, and do not need to be wrapped with
``@ayncio.coroutine`` to use the usual ``yield from`` functionality.  It's
perfectly fine to make them coroutines, or not - all non-couroutines will be
wrapped, and will simply execute synchronously.  This allows those who want to
take advantage of the async framework to do so, without adding syntactical
overhead for those that don't need such features.

Pseudocode::

    event_name
    return lambda function_to_wrap:
        try:
            register_for_event(event_name, function_to_wrap)
        except invalid_arguments:
            raise

Client.trigger
--------------

*This is a coroutine.*

TODO: Document trigger (manual injection of command/reply)

Client.connect
--------------

*This is a coroutine.*

Attempt to reconnect using the client's host, port.  This is a passthrough to
the underlying Connection.  Because it is a coroutine, you MUST invoke this
using ``yield from``.  As mentioned above, don't worry about calling
``yield from Client.connect()`` in a function - any functions registered with
the event handler will make sure it wraps synchronous functions in a coroutine.

Client.disconnect
-----------------

*This is a coroutine.*

Disconnect from the server if connected.  This is a passthrough to the
underlying Connection.  Because it is a coroutine, you MUST invoke this using
``yield from``.  As mentioned above, don't worry about calling
``yield from Client.connect()`` in a function - any functions registered with
the event handler will make sure it wraps synchronous functions in a coroutine.

Client.send
-----------

Send a command to the server.  The available kwargs are documented below.

Some examples::

    Client.send('join', channel='#python')
        --> "JOIN #python"
    Client.send('privmsg', target='#python', message="Hello!")
        --> "PRIVMSG #python :Hello!"
    Client.send('privmsg', target='super_trooper_23',
                message='you are freaking out... man.')
        --> "PRIVMSG super_trooper_23 :you are freaking out... man."

Other Classes and Modules
-------------------------

The ``unpack`` module is used to unpack an irc line into the appropriate named
objects based on the command's grammar.  It also houses the synonyms table for
converting numeric responses to their equivalent string representations.

The ``pack`` module is used to pack an irc command and paramaters into the
appropriate wire format based on the command's grammar.

The ``Connection`` class handles the main read loop, connecting and
disconnecting from the server, and sending raw strings to the server.

The ``event`` module contains the ``EventsMixin`` class which registers
handlers and invokes them when the corresponding event is triggered.  It is
used by the ``@Client.on`` decorator.  It does some optimization using the
``partial_bind`` function to speed up argument injection.

Supported Commands
==================

Send (``Client.send`` or ``Client.trigger``)
--------------------------------------------

* Local Events *(trigger only)*

  * CLIENT_CONNECT
  * CLIENT_DISCONNECT

* `Connection Registration`_

  * PASS
  * NICK
  * USER
  * OPER
  * USERMODE (renamed from MODE)
  * SERVICE
  * QUIT
  * SQUIT

* `Channel Operations`_

  * JOIN
  * PART
  * CHANNELMODE (renamed from MODE)
  * TOPIC
  * NAMES
  * LIST
  * INVITE
  * KICK

* `Sending Messages`_

  * PRIVMSG
  * NOTICE

* `Server Queries and Commands`_

  * MOTD
  * LUSERS
  * VERSION
  * STATS
  * LINKS
  * TIME
  * CONNECT
  * TRACE
  * ADMIN
  * INFO

* `Service Query and Commands`_

  * SERVLIST
  * SQUERY

* `User Based Queries`_

  * WHO
  * WHOIS
  * WHOWAS

* `Miscellaneous Messages`_

  * KILL
  * PONG

* `Optional Features`_

  * AWAY
  * REHASH
  * DIE
  * RESTART
  * SUMMON
  * USERS
  * WALLOPS
  * USERHOST
  * ISON*

.. _Connection Registration:
    https://tools.ietf.org/html/rfc2812#section-3.1
.. _Channel Operations:
    https://tools.ietf.org/html/rfc2812#section-3.2
.. _Sending Messages:
    https://tools.ietf.org/html/rfc2812#section-3.3
.. _Server Queries and Commands:
    https://tools.ietf.org/html/rfc2812#section-3.4
.. _Service Query and Commands:
    https://tools.ietf.org/html/rfc2812#section-3.5
.. _User Based Queries:
    https://tools.ietf.org/html/rfc2812#section-3.6
.. _Miscellaneous Messages:
    https://tools.ietf.org/html/rfc2812#section-3.7
.. _Optional Features:
    https://tools.ietf.org/html/rfc2812#section-4

Events (``@Client.on``)
------------------------
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

Command Parameters
==================

Send
--------------------------------------------

This section will eventually list the required/optional parameters for each
command, their types, and their defaults.

Events
------------------------

This section will eventually list the available parameters for each command or
reply, and their types.

Contributing
============

Any contribution is welcome!  The TODO below is simply a guide for getting to
1.0.0

Development
-----------

bottom uses ``tox``, ``pytest`` and ``flake8``.  To get everything set up::

    # RECOMMENDED: create a virtualenv
    # mkvirtualenv bottom
    git clone https://github.com/numberoverzero/bottom.git
    pip install tox
    tox

Please make sure ``tox`` passes (including flake8) before submitting a PR.
It's ok if tox doesn't pass, but it makes it much easier (and faster) if it
does.

TODO
----

#. Resolve open diversions from rfc2812 in ``pack.py:pack_command``

   #. Add ``target`` argument for all listed operations
   #. Implement ``PING`` and ``ERROR`` (How do these work client -> server?)
   #. Add boolean flag for ``WHO``?  How do present/missing flags fit in the API?

#. Add missing replies/errors to ``unpack.py:unpack_command``

   #. Add reply/error parameters to ``unpack.py:parameters``
   #. Remove ``Client.logger`` when all rfc2812 replies implemented

#. Better ``Client`` docstrings

   #. Review source for command/event consistency

#. Expand README

   #. Client.trigger
   #. Command Parameters -> Send
   #. Command Parameters -> Events

