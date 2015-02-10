# bottom 0.9.11

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

bottom isn't a kitchen-sink library.  Instead, it provides a consistent API with a small surface area, tuned for performance and ease of extension.  Similar to the routing style of bottle.py, hooking into events is one line.

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

# Versioning  and RFC2812

* Bottom follows semver for its **public** API.

  * Currently, `Client` is the only public member of bottom.
  * IRC replies/codes which are not yet implemented may be added at any time, and will correspond to a patch - the function contract of `@on` method does not change.
  * You should not rely on the internal api staying the same between minor versions.
  * Over time, private apis may be raised to become public.  The reverse will never occur.

* There are a number of changes from RFC2812 - none should noticeably change how you interact with a standard IRC server.  For specific adjustments, see the notes section of each command in [`Supported Commands`](#supported-commands).

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
* Better `Client` docstrings
* Add missing replies/errors to `unpack.py:unpack_command`
  * Add reply/error parameters to `unpack.py:parameters`
  * Remove `Client.logger` when all rfc2812 replies implemented
  * Document [`Supported Events`](#supported-events)

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

VAR_KWARGS can be used, as long as the name doesn't mask an actual parameter.  VAR_ARGS may not be used.

```python
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
```

Decorated functions will be invoked asynchronously, and may optionally use the `yield from` syntax.  Functions do not need to be wrapped with `@ayncio.coroutine` - this is handled as part of the function caching process.

### Client.trigger(event, **kwargs)

*This is a coroutine.*

Manually inject a command or reply as if it came from the server.  This is useful for invoking other handlers.

```python
# Manually trigger `PRIVMSG` handlers:
yield from bot.trigger('privmsg', nick="always_says_no", message="yes")
```

```python
# Rename !commands to !help
@bot.on('privmsg')
def parse(nick, target, message):
    if message == '!commands':
        bot.send('privmsg', target=nick,
                 message="!commands was renamed to !help in 1.2")
        # Don't make them retype it, just make it happen
        yield from bot.trigger('privmsg', nick=nick,
                               target=target, message="!help")
```

```python
# While testing the auto-reconnect module, simulate a disconnect:
def test_reconnect(bot):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.trigger("client_disconnect"))
    assert bot.connected
```

### Client.connect()

*This is a coroutine.*

Attempt to reconnect using the client's host, port.

```python
@bot.on('client_disconnect')
def reconnect():
    # Wait a few seconds
    yield from asyncio.sleep(3)
    yield from bot.connect()
```

### Client.disconnect()

*This is a coroutine.*

Disconnect from the server if connected.

```python
@bot.on('privmsg')
def suicide_pill(nick, message):
    if nick == "spy_handler" and message == "last stop":
        yield from bot.disconnect()
```

### Client.send(command, **kwargs)

Send a command to the server.  See [`Supported Commands`](#supported-commands) for a detailed breakdown of available commands and their parameters.

# Supported Commands

These commands can be sent to the server using [`Client.send`](#clientsendcommand-kwargs).

For incoming signals and messages, see [`Supported Events`](#supported-events) below.

#### Documentation Layout
There are three parts to each command's documentation:

1. **Python syntax** - sample calls using available parameters
2. **Normalized IRC wire format** - the normalized translation from python keywords to a literal string that will be constructed by the client and sent to the server.  The following syntax is used:
  * `<parameter>` the location of the `parameter` passed to `send`.  Literal `<>` are not transferred.
  * `[value]` an optional value, which may be excluded.  In some cases, such as [`LINKS`](#links), an optional value may only be provided if another dependant value is present.  Literal `[]` are not transferred.
  * `:` the start of a field which may contain spaces.  This is always the last field of an IRC line.
  * `"value"` literal value as printed.  Literal `""` are not transferred.
3. **Notes** - additional options or restrictions on commands that do not fit a pre-defined convention.  Common notes include keywords for ease of searching:
  * `RFC_DELTA` - Some commands have different parameters from their RFC2812 definitions.  **Please pay attention to these notes, since they are the most likely to cause issues**.  These changes can include:
    * Addition of new required or optional parameters
    * Default values for new or existing parameters
  * `CONDITIONAL_OPTION` - there are some commands whose values depend on each other.  For example, [`LINKS`](#links), `<mask>` REQUIRES `<remote>`.
  * `MULTIPLE_VALUES` - Some commands can handle non-string iterables, such as [`WHOWAS`](#whowas) where `<nick>` can handle both `"WiZ"` and `["WiZ", "WiZ-friend"]`.
  * `PARAM_RENAME` - Some commands have renamed parameters from their RFC2812 specification to improve comsistency.

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

## Connection Registration
#### [PASS]
```python
client.send('PASS', password='hunter2')
```

    PASS <password>

#### [NICK]
```python
client.send('nick', nick='WiZ')
```

    NICK <nick>

* PARAM_RENAME `nickname -> nick`

#### [USER]
```python
client.send('USER', user='WiZ-user', realname='Ronnie')
client.send('USER', user='WiZ-user', mode='8', realname='Ronnie')
```

    USER <user> [<mode>] :<realname>

* RFC_DELTA `mode` is optional - default is `0`

#### [OPER]
```python
client.send('OPER', user='WiZ', password='hunter2')
```

    OPER <user> <password>

* PARAM_RENAME `name -> user`

#### [USERMODE][USERMODE] (renamed from [MODE][USERMODE])
```python
client.send('USERMODE', nick='WiZ')
client.send('USERMODE', nick='WiZ', modes='+io')
```

    MODE <nick> [<modes>]

* RFC_DELTA rfc did not name `modes` parameter

#### [SERVICE]
```python
client.send('SERVICE', nick='CHANSERV', distribution='*.en',
            type='0', info='manages channels')
```

    SERVICE <nick> <distribution> <type> :<info>

* PARAM_RENAME `nickname -> nick`

#### [QUIT]
```python
client.send('QUIT')
client.send('QUIT', message='Gone to Lunch')
```

    QUIT :[<message>]

* PARAM_RENAME `Quit Message -> message`

#### [SQUIT]
```python
client.send('SQUIT', server='tolsun.oulu.fi')
client.send('SQUIT', server='tolsun.oulu.fi', message='Bad Link')
```

    SQUIT <server> :[<message>]

* PARAM_RENAME `Comment -> message`
* RFC_DELTA `message` is optional - rfc says comment SHOULD be supplied; syntax shows required

## Channel Operations

#### [JOIN]
```python
client.send('JOIN', channel='0')  # send PART to all joined channels
client.send('JOIN', channel='#foo-chan')
client.send('JOIN', channel='#foo-chan', key='foo-key')
client.send('JOIN', channel=['#foo-chan', '#other'], key='key-for-both')
client.send('JOIN', channel=['#foo-chan', '#other'], key=['foo-key', 'other-key'])
```

    JOIN <channel> [<key>]

* MULTIPLE_VALUES `channel` and `key`
* If `channel` has n > 1 values, `key` MUST have 1 or n values

#### [PART]
```python
client.send('PART', channel='#foo-chan')
client.send('PART', channel=['#foo-chan', '#other'])
client.send('PART', channel='#foo-chan', message='I lost')
```

    PART <channel> :[<message>]

* MULTIPLE_VALUES `channel`

#### [CHANNELMODE][CHANNELMODE] (renamed from [MODE][CHANNELMODE])
```python
client.send('CHANNELMODE', channel='#foo-chan', modes='+b')
client.send('CHANNELMODE', channel='#foo-chan', modes='+l', params='10')
```

    MODE <channel> <modes> [<params>]

* PARAM_RENAME `modeparams -> params`

#### [TOPIC]
```python
client.send('TOPIC', channel='#foo-chan')
client.send('TOPIC', channel='#foo-chan', message='')  # Clear channel message
client.send('TOPIC', channel='#foo-chan', message='Yes, this is dog')
```

    TOPIC <channel> :[<message>]

* PARAM_RENAME `topic -> message`

#### [NAMES]
```python
client.send('NAMES')
client.send('NAMES', channel='#foo-chan')
client.send('NAMES', channel=['#foo-chan', '#other'])
client.send('NAMES', channel=['#foo-chan', '#other'], target='remote.*.edu')
```

    NAMES [<channel>] [<target>]

* MULTIPLE_VALUES `channel`
* CONDITIONAL_OPTION `target` requires `channel`

#### [LIST]
```python
client.send('LIST')
client.send('LIST', channel='#foo-chan')
client.send('LIST', channel=['#foo-chan', '#other'])
client.send('LIST', channel=['#foo-chan', '#other'], target='remote.*.edu')
```

    LIST [<channel>] [<target>]

* MULTIPLE_VALUES `channel`
* CONDITIONAL_OPTION `target` requires `channel`

#### [INVITE]
```python
client.send('INVITE', nick='WiZ-friend', channel='#bar-chan')
```

    INVITE <nick> <channel>

* PARAM_RENAME `nickname -> nick`

#### [KICK]
```python
client.send('KICK', channel='#foo-chan', nick='WiZ')
client.send('KICK', channel='#foo-chan', nick='WiZ', message='Spamming')
client.send('KICK', channel='#foo-chan', nick=['WiZ', 'WiZ-friend'])
client.send('KICK', channel=['#foo', '#bar'], nick=['WiZ', 'WiZ-friend'])
```

    KICK <channel> <nick> :[<message>]

* PARAM_RENAME `nickname -> nick`
* PARAM_RENAME `comment -> message`
* MULTIPLE_VALUES `channel` and `nick`
* If `nick` has n > 1 values, channel MUST have 1 or n values
* `channel` can have n > 1 values IFF `nick` has n values

## Sending Messages
#### [PRIVMSG]
```python
client.send('PRIVMSG', target='WiZ-friend', message='Hello, friend!')
```

    PRIVMSG <target> :<message>

* PARAM_RENAME `msgtarget -> target`
* PARAM_RENAME `text to be sent -> message`

#### [NOTICE]
```python
client.send('NOTICE', target='#foo-chan', message='Maintenance in 5 mins')
```

    NOTICE <target> :<message>

* PARAM_RENAME `msgtarget -> target`
* PARAM_RENAME `text -> message`

## Server Queries and Commands
#### [MOTD]
```python
client.send('MOTD')
client.send('MOTD', target='remote.*.edu')
```

    MOTD [<target>]

#### [LUSERS]
```python
client.send('LUSERS')
client.send('LUSERS', mask='*.edu')
client.send('LUSERS', mask='*.edu', target='remote.*.edu')
```

    LUSERS [<mask>] [<target>]

* CONDITIONAL_OPTION `target` requires `mask`

#### [VERSION]
```python
client.send('VERSION')
```

    VERSION [<target>]

#### [STATS]
```python
client.send('STATS')
client.send('STATS', query='m')
client.send('STATS', query='m', target='remote.*.edu')
```

    STATS [<query>] [<target>]

* CONDITIONAL_OPTION `target` requires `query`

#### [LINKS]
```python
client.send('LINKS')
client.send('LINKS', mask='*.bu.edu')
client.send('LINKS', remote='*.edu', mask='*.bu.edu')
```

    LINKS [<remote>] [<mask>]

* PARAM_RENAME `remote server -> remote`
* PARAM_RENAME `server mask -> mask`
* CONDITIONAL_OPTION `remote` requires `mask`

#### [TIME]
```python
client.send('TIME')
client.send('TIME', target='remote.*.edu')
```

    TIME [<target>]

#### [CONNECT]
```python
client.send('CONNECT', target='tolsun.oulu.fi', port=6667)
client.send('CONNECT', target='tolsun.oulu.fi', port=6667, remote='*.edu')
```

    CONNECT <target> <port> [<remote>]

* PARAM_RENAME `target server -> target`
* PARAM_RENAME `remote server -> remote`

#### [TRACE]
```python
client.send('TRACE')
client.send('TRACE', target='remote.*.edu')
```

    TRACE [<target>]

#### [ADMIN]
```python
client.send('ADMIN')
client.send('ADMIN', target='remote.*.edu')
```

    ADMIN [<target>]

#### [INFO]
```python
client.send('INFO')
client.send('INFO', target='remote.*.edu')
```

    INFO [<target>]

## Service Query and Commands
#### [SERVLIST]
```python
client.send('SERVLIST', mask='*SERV')
client.send('SERVLIST', mask='*SERV', type=3)
```

    SERVLIST [<mask>] [<type>]

* CONDITIONAL_OPTION `type` requires `mask`

#### [SQUERY]
```python
client.send('SQUERY', target='irchelp', message='HELP privmsg')
```

    SQUERY <target> :<message>

* PARAM_RENAME `servicename -> target`
* PARAM_RENAME `text -> message`

## User Based Queries
#### [WHO]
```python
client.send('WHO')
client.send('WHO', mask='*.fi')
client.send('WHO', mask='*.fi', o=True)
```

    WHO [<mask>] ["o"]

* Optional positional parameter "o" is included if the kwarg "o" is Truthy

#### [WHOIS]
```python
client.send('WHOIS', mask='*.fi')
client.send('WHOIS', mask=['*.fi', '*.edu'], target='remote.*.edu')
```

    WHOIS <mask> [<target>]

* MULTIPLE_VALUES `mask`

#### [WHOWAS]
```python
client.send('WHOWAS', nick='WiZ')
client.send('WHOWAS', nick='WiZ', count=10)
client.send('WHOWAS', nick=['WiZ', 'WiZ-friend'], count=10)
client.send('WHOWAS', nick='WiZ', count=10, target='remote.*.edu')
```

    WHOWAS <nick> [<count>] [<target>]

* PARAM_RENAME `nickname -> nick`
* MULTIPLE_VALUES `nick`
* CONDITIONAL_OPTION `target` requires `count`

## Miscellaneous Messages
#### [KILL]
```python
client.send('KILL', nick='WiZ', message='Spamming Joins')
```

    KILL <nick> :<message>

* PARAM_RENAME `nickname -> nick`
* PARAM_RENAME `comment -> message`

#### [PING]
```python
client.send('PING', message='Test..')
client.send('PING', server2='tolsun.oulu.fi')
client.send('PING', server1='WiZ', server2='tolsun.oulu.fi')
```

    PING [<server1>] [<server2>] :[<message>]

* RFC_DELTA `server1` is optional
* RFC_DELTA `message` is new, and optional
* CONDITIONAL_OPTION `server2` requires `server1`

#### [PONG]
```python
client.send('PONG', message='Test..')
client.send('PONG', server2='tolsun.oulu.fi')
client.send('PONG', server1='WiZ', server2='tolsun.oulu.fi')
```

    PONG [<server1>] [<server2>] :[<message>]

* RFC_DELTA `server1` is optional
* RFC_DELTA `message` is new, and optional
* CONDITIONAL_OPTION `server2` requires `server1`

## Optional Features
#### [AWAY]
```python
client.send('AWAY')
client.send('AWAY', message='Gone to Lunch')
```

    AWAY :[<message>]

* PARAM_RENAME `text -> message`

#### [REHASH]
```python
client.send('REHASH')
```

    REHASH

#### [DIE]
```python
client.send('DIE')
```

    DIE

#### [RESTART]
```python
client.send('RESTART')
```

    RESTART

#### [SUMMON]
```python
client.send('SUMMON', nick='WiZ')
client.send('SUMMON', nick='WiZ', target='remote.*.edu')
client.send('SUMMON', nick='WiZ', target='remote.*.edu', channel='#foo-chan')
```

    SUMMON <nick> [<target>] [<channel>]

* PARAM_RENAME `user -> nick`
* CONDITIONAL_OPTION `channel` requires `target`

#### [USERS]
```python
client.send('USERS')
client.send('USERS', target='remote.*.edu')
```

    USERS [<target>]

#### [WALLOPS]
```python
client.send('WALLOPS', message='Maintenance in 5 minutes')
```

    WALLOPS :<message>

* PARAM_RENAME `Text to be sent -> message`

#### [USERHOST]
```python
client.send('USERHOST', nick='WiZ')
client.send('USERHOST', nick=['WiZ', 'WiZ-friend'])
```

    USERHOST <nick>

* PARAM_RENAME `nickname -> nick`
* MULTIPLE_VALUES `nick`

#### [ISON]
```python
client.send('ISON', nick='WiZ')
client.send('ISON', nick=['WiZ', 'WiZ-friend'])
```

    ISON <nick>

* PARAM_RENAME `nickname -> nick`
* MULTIPLE_VALUES `nick`

[PASS]: https://tools.ietf.org/html/rfc2812#section-3.1.1
[NICK]: https://tools.ietf.org/html/rfc2812#section-3.1.2
[USER]: https://tools.ietf.org/html/rfc2812#section-3.1.3
[OPER]: https://tools.ietf.org/html/rfc2812#section-3.1.4
[USERMODE]: https://tools.ietf.org/html/rfc2812#section-3.1.5
[SERVICE]: https://tools.ietf.org/html/rfc2812#section-3.1.6
[QUIT]: https://tools.ietf.org/html/rfc2812#section-3.1.7
[SQUIT]: https://tools.ietf.org/html/rfc2812#section-3.1.8

[JOIN]: https://tools.ietf.org/html/rfc2812#section-3.2.1
[PART]: https://tools.ietf.org/html/rfc2812#section-3.2.2
[CHANNELMODE]: https://tools.ietf.org/html/rfc2812#section-3.2.3
[TOPIC]: https://tools.ietf.org/html/rfc2812#section-3.2.4
[NAMES]: https://tools.ietf.org/html/rfc2812#section-3.2.5
[LIST]: https://tools.ietf.org/html/rfc2812#section-3.2.6
[INVITE]: https://tools.ietf.org/html/rfc2812#section-3.2.7
[KICK]: https://tools.ietf.org/html/rfc2812#section-3.2.8

[PRIVMSG]: https://tools.ietf.org/html/rfc2812#section-3.3.1
[NOTICE]: https://tools.ietf.org/html/rfc2812#section-3.3.2

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

[SERVLIST]: https://tools.ietf.org/html/rfc2812#section-3.5.1
[SQUERY]: https://tools.ietf.org/html/rfc2812#section-3.5.2

[WHO]: https://tools.ietf.org/html/rfc2812#section-3.6.1
[WHOIS]: https://tools.ietf.org/html/rfc2812#section-3.6.2
[WHOWAS]: https://tools.ietf.org/html/rfc2812#section-3.6.3

[KILL]: https://tools.ietf.org/html/rfc2812#section-3.7.1
[PING]: https://tools.ietf.org/html/rfc2812#section-3.7.2
[PONG]: https://tools.ietf.org/html/rfc2812#section-3.7.3

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

These commands are received from the server, or dispatched using `Client.trigger(...)`.

For sending commands, see [`Supported Commands`](#supported-commands) above.

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
