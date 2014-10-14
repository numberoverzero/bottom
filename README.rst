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
considered private except the ``Client`` class.

Versioning
----------

bottom strictly follows semver for its public API.  All private methods are
subject to change at any time, and will correspond to a patch.  I have no
moral qualms with a version 7.0 or 23.1, and the **public** api (currently,
only the ``Client`` class) will adhere strictly to this.

You should not rely on the behavior of any internal methods staying the same
between minor versions, or even patches.

A quick reminder:

* **MAJOR** - Backwards incompatible in at least 1 way with the previous MAJOR
  version.
* **MINOR** - New functionality introduced, in a backwards-compatible way.
* **PATCH** - Backwards-compatible

The only anticipated change will (possibly) be to ``Client.send`` before the
1.0.0 release.  The rest of the API should be considered stable, bar major
complaints.

Client.run
----------

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

Client.connect
--------------

`This is a coroutine.`

Attempt to reconnect using the client's host, port.  This is a passthrough to
the underlying Connection.  Because it is a coroutine, you MUST invoke this
using ``yield from``.  As mentioned above, don't worry about calling
``yield from Client.connect()`` in a function - any functions registered with
the event handler will make sure it wraps synchronous functions in a coroutine.

Client.disconnect
-----------------

`This is a coroutine.`

Disconnect from the server if connected.  This is a passthrough to the
underlying Connection.  Because it is a coroutine, you MUST invoke this using
``yield from``.  As mentioned above, don't worry about calling
``yield from Client.connect()`` in a function - any functions registered with
the event handler will make sure it wraps synchronous functions in a coroutine.

Client.send
-----------

**API NOT FINAL** - see note below.

Send a command to the server.  Any additional arguments will be sent as
parameters for the command - a prefix for the command, as well as a message,
can also be specified.

Some examples::

    Client.send('join', '#python')
        --> "JOIN #python"
    Client.send('privmsg', 'pypi', '#python', message="Hello!")
        --> "PRIVMSG pypi #python :Hello!"
    Client.send('privmsg', '#troopers', prefix='rabbit!st3@vermont',
                message='you are freaking out... man.')
        --> ":rabbit!st3@vermont PRIVMSG #troopers :you are freaking out... man."

**API NOT FINAL**

This is the only function that *may* change.  It still feels a bit low-level,
and I think there's room to make it smarter about IRC commands, or less
ambiguous about ordering.  For example, always taking a command + dict whose
keys map to the equivalent values output by that command would remove the
possible confusion around determining parameters automatically but requiring an
explicit ``message=``.  For example, a PRIVMSG would be::

    Client.send('privmsg', {'message': 'Hello, World', 'target': '#python'})

Or a PONG would be::

    Client.send('PONG', {'message': 'original ping message'})

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
