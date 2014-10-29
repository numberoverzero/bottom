# bottom 0.9.3

[![Build Status]
(https://travis-ci.org/numberoverzero/bottom.svg?branch=master)]
(https://travis-ci.org/numberoverzero/bottom)[![Coverage Status]
(https://coveralls.io/repos/numberoverzero/bottom/badge.png?branch=master)]
(https://coveralls.io/r/numberoverzero/bottom?branch=master)

Downloads https://pypi.python.org/pypi/bottom
Source https://github.com/numberoverzero/bottom

asyncio-based rfc2812-compliant IRC Client

# Installation

`pip install bottom`

# Getting Started

bottom isn't a kitchen-sink library.  Instead, it provides an API with a small surface area, tuned for performance and ease of extension.  Similar to the routing style of bottle.py, hooking into events is one line.

```python
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
```

# Versioning

* Bottom follows semver for its **public** API.

  * Currently, `Client` is the only public member of bottom.
  * IRC replies/codes which are not yet implemented may be added at any time, and will correspond to a patch.  The contract of the `@on` method does not change - this is only an expansion of legal inputs.

* There are a number of unsupported parameters for IRC commands defined in rfc2812 which should be added.  The list of all adjustments can be found in `bottom/pack.py` in the notes of `pack_command`.  Any changes listed below will be made before 1.0.0, if they occur at all.

  * RENAMES will not change.
  * MODE is split into USERMODE and CHANNELMODE and will not change.
  * Any command that doesn't use the `<target>` parameter will be updated to use it by 1.0.0
  * WHO may get a boolean 'o' parameter
  * PING and PONG have an optional parameter `message` although not formally defined in rfc2812.

* All private methods are subject to change at any time, and will correspond to a patch.

  * You should not rely on the api of any internal methods staying the same between minor versions.

* Over time, private apis may be raised to become public.  The reverse will never occur.

# Contributing
Contributions welcome!  Please make sure `tox` passes (including flake8) before submitting a PR.

### Development
bottom uses `tox`, `pytest` and `flake8`.  To get everything set up:

```
# RECOMMENDED: create a virtualenv with:
#     mkvirtualenv bottom
git clone https://github.com/numberoverzero/bottom.git
pip install tox
tox
```

### TODO
* Resolve open diversions from rfc2812 in `pack.py:pack_command`
  * Add `target` argument for all listed operations
  * Add boolean flag for `WHO`?  How do present/missing flags fit in the API?
* Add missing replies/errors to `unpack.py:unpack_command`
  * Add reply/error parameters to `unpack.py:parameters`
  * Remove `Client.logger` when all rfc2812 replies implemented
* Better `Client` docstrings
  * Review source for command/event consistency
* Expand README
  * Client.trigger
  * Command Parameters -> Send
  * Command Parameters -> Events

# API

### Client.run()

*This is a coroutine.*

Start the magic.  This will connect the client, and then read until it disconnects.  The `CLIENT_DISCONNECT` event will fire before the loop exits, allowing you to `yield from Client.connect()` and keep the client running.

If you want to call this synchronously (block until it's complete) use the following:

```python
import asyncio
# ... client is defined somewhere

loop = asyncio.get_event_loop()
task = client.run()
loop.run_until_complete(task)
```

### Client.on(event)(func)

This `@decorator` is the main way you'll interact with a `Client`.  It takes a string, returning a function wrapper that validates the function and registers it for the given event.  When that event occurs, the function will be called, mapping any arguments the function may expect from the set of available arguments for the event.

Not all available arguments need to be used.  For instance, both of the following are valid:

```python
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
```

VAR_KWARGS can be used, as long as the name doesn't mask an actual field.

The following is ok:

```python
@bot.on('PRIVMSG')
def event(message, **everything_else):
    logger.log(everything_else['nick'] + " said " + message)
```

But this is not:

```python
@bot.on('PRIVMSG')
def event(message, **nick):
    logger.log(nick['target'])
```

VAR_ARGS may not be used.  This will raise:

```python
@bot.on('PRIVMSG')
def event(message, *args):
    logger.log(args)
```

Decorated functions will be invoked asynchronously, and may optionally use the `yield from` syntax.  Functions do not need to be wrapped with `@ayncio.coroutine` - this is handled as part of the function caching process.

### Client.trigger(event, **kwargs)

*This is a coroutine.*

Manually inject a command or reply as if it came from the server.  This is useful for invoking other handlers.

Trigger `PRIVMSG` handlers:

    yield from bot.trigger('privmsg', nick="always_says_no", message="yes")

Rename !commands to !help:

```python
@bot.on('privmsg')
def parse(nick, target, message):
    if message == '!commands':
        bot.send('privmsg', target=nick,
                 message="!commands was renamed to !help in 1.2")
        # Don't make them retype it, just make it happen
        yield from bot.trigger('privmsg', nick=nick,
                               target=target, message="!help")
```

While testing the auto-reconnect module, simulate a disconnect:

```python
def test_reconnect(bot):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.trigger("client_disconnect"))
    assert bot.connected
```

### Client.connect()

*This is a coroutine.*

Attempt to reconnect using the client's host, port.  This is a passthrough to the underlying Connection.  Because it is a coroutine, you MUST invoke this using `yield from`.  As mentioned above, don't worry about calling `yield from Client.connect()` in a function - any functions registered with the event handler will make sure it wraps synchronous functions in a coroutine.

### Client.disconnect()

*This is a coroutine.*

Disconnect from the server if connected.  This is a passthrough to the underlying Connection.  Because it is a coroutine, you MUST invoke this using `yield from`.  As mentioned above, don't worry about calling `yield from Client.connect()` in a function - any functions registered with the event handler will make sure it wraps synchronous functions in a coroutine.

### Client.send(command, **kwargs)

Send a command to the server.  The available kwargs are documented below.

Some examples of how `send` maps to raw IRC lines:

```python
Client.send('join', channel='#python')
    --> "JOIN #python"
Client.send('privmsg', target='#python', message="Hello!")
    --> "PRIVMSG #python :Hello!"
Client.send('privmsg', target='super_trooper_23',
            message='you are freaking out... man.')
    --> "PRIVMSG super_trooper_23 :you are freaking out... man."
```

# Supported Commands

These commands can be sent to the server using `Client.send(...)`.  For incoming signals and messages, see `Supported Events` below.

## Local Events
*(trigger only)*

#### CLIENT_CONNECT
```python
yield from client.trigger('CLIENT_CONNECT', host='localhost', port=6697)
```
#### CLIENT_DISCONNECT
```python
yield from client.trigger('CLIENT_DISCONNECT', host='localhost', port=6697)
```

## [Connection Registration]
#### [PASS]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [NICK]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [USER]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [OPER]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [USERMODE] (renamed from [MODE][USERMODE])
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [SERVICE]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [QUIT]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [SQUIT]
```python
client.send('PASS', password='hunter2')
```

    PASS password


## [Channel Operations]
#### [JOIN]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [PART]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [CHANNELMODE] (renamed from [MODE][CHANNELMODE])
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [TOPIC]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [NAMES]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [LIST]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [INVITE]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [KICK]
```python
client.send('PASS', password='hunter2')
```

    PASS password

## [Sending Messages]
#### [PRIVMSG]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [NOTICE]
```python
client.send('PASS', password='hunter2')
```

    PASS password

## [Server Queries and Commands]
#### [MOTD]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [LUSERS]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [VERSION]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [STATS]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [LINKS]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [TIME]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [CONNECT]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [TRACE]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [ADMIN]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [INFO]
```python
client.send('PASS', password='hunter2')
```

    PASS password

## [Service Query and Commands]
#### [SERVLIST]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [SQUERY]
```python
client.send('PASS', password='hunter2')
```

    PASS password

## [User Based Queries]
#### [WHO]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [WHOIS]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [WHOWAS]
```python
client.send('PASS', password='hunter2')
```

    PASS password

## [Miscellaneous Messages]
#### [KILL]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [PING]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [PONG]
```python
client.send('PASS', password='hunter2')
```

    PASS password

## [Optional Features]
#### [AWAY]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [REHASH]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [DIE]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [RESTART]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [SUMMON]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [USERS]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [WALLOPS]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [USERHOST]
```python
client.send('PASS', password='hunter2')
```

    PASS password

#### [ISON]
```python
client.send('PASS', password='hunter2')
```

    PASS password


[Connection Registration]: https://tools.ietf.org/html/rfc2812#section-3.1
[PASS]: https://tools.ietf.org/html/rfc2812#section-3.1.1
[NICK]: https://tools.ietf.org/html/rfc2812#section-3.1.2
[USER]: https://tools.ietf.org/html/rfc2812#section-3.1.3
[OPER]: https://tools.ietf.org/html/rfc2812#section-3.1.4
[USERMODE]: https://tools.ietf.org/html/rfc2812#section-3.1.5
[SERVICE]: https://tools.ietf.org/html/rfc2812#section-3.1.6
[QUIT]: https://tools.ietf.org/html/rfc2812#section-3.1.7
[SQUIT]: https://tools.ietf.org/html/rfc2812#section-3.1.8

[Channel Operations]: https://tools.ietf.org/html/rfc2812#section-3.2
[JOIN]: https://tools.ietf.org/html/rfc2812#section-3.2.1
[PART]: https://tools.ietf.org/html/rfc2812#section-3.2.2
[CHANNELMODE]: https://tools.ietf.org/html/rfc2812#section-3.2.3
[TOPIC]: https://tools.ietf.org/html/rfc2812#section-3.2.4
[NAMES]: https://tools.ietf.org/html/rfc2812#section-3.2.5
[LIST]: https://tools.ietf.org/html/rfc2812#section-3.2.6
[INVITE]: https://tools.ietf.org/html/rfc2812#section-3.2.7
[KICK]: https://tools.ietf.org/html/rfc2812#section-3.2.8

[Sending Messages]: https://tools.ietf.org/html/rfc2812#section-3.3
[PRIVMSG]: https://tools.ietf.org/html/rfc2812#section-3.3.1
[NOTICE]: https://tools.ietf.org/html/rfc2812#section-3.3.2

[Server Queries and Commands]: https://tools.ietf.org/html/rfc2812#section-3.4
[MOTD]: https://tools.ietf.org/html/rfc2812#section-3.4.1
[LUSERS]: https://tools.ietf.org/html/rfc2812#section-3.4.2
[VERSION]: https://tools.ietf.org/html/rfc2812#section-3.4.3
[STATS]: https://tools.ietf.org/html/rfc2812#section-3.4.4
[LINKS]: https://tools.ietf.org/html/rfc2812#section-3.4.5
[TIME]: https://tools.ietf.org/html/rfc2812#section-3.4.6
[CONNECT]: https://tools.ietf.org/html/rfc2812#section-3.4.7
[TRACE]: https://tools.ietf.org/html/rfc2812#section-3.4.8
[ADMIN]: https://tools.ietf.org/html/rfc2812#section-3.4.9
[INFO]: https://tools.ietf.org/html/rfc2812#section-3.4.10

[Service Query and Commands]: https://tools.ietf.org/html/rfc2812#section-3.5
[SERVLIST]: https://tools.ietf.org/html/rfc2812#section-3.5.1
[SQUERY]: https://tools.ietf.org/html/rfc2812#section-3.5.2

[User Based Queries]: https://tools.ietf.org/html/rfc2812#section-3.6
[WHO]: https://tools.ietf.org/html/rfc2812#section-3.6.1
[WHOIS]: https://tools.ietf.org/html/rfc2812#section-3.6.2
[WHOWAS]: https://tools.ietf.org/html/rfc2812#section-3.6.3

[Miscellaneous Messages]: https://tools.ietf.org/html/rfc2812#section-3.7
[KILL]: https://tools.ietf.org/html/rfc2812#section-3.7.1
[PING]: https://tools.ietf.org/html/rfc2812#section-3.7.2
[PONG]: https://tools.ietf.org/html/rfc2812#section-3.7.3

[Optional Features]: https://tools.ietf.org/html/rfc2812#section-4
[AWAY]: https://tools.ietf.org/html/rfc2812#section-4.1
[REHASH]: https://tools.ietf.org/html/rfc2812#section-4.2
[DIE]: https://tools.ietf.org/html/rfc2812#section-4.3
[RESTART]: https://tools.ietf.org/html/rfc2812#section-4.4
[SUMMON]: https://tools.ietf.org/html/rfc2812#section-4.5
[USERS]: https://tools.ietf.org/html/rfc2812#section-4.6
[WALLOPS]: https://tools.ietf.org/html/rfc2812#section-4.7
[USERHOST]: https://tools.ietf.org/html/rfc2812#section-4.8
[ISON]: https://tools.ietf.org/html/rfc2812#section-4.9


# Supported Events

These commands are received from the server, or dispatched using `Client.trigger(...)`.  For sending commands, see `Supported Commands` above.

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
