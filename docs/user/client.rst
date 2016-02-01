Client
======

TODO: Document ``@on``, ``async connect``, ``async disconnect``, ``async wait``

Client.send Commands
--------------------

TODO: Short blurb for optional vs required for each

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

Client.trigger Events
---------------------

TODO: List kwargs for each event

::

    # Local only events
    CLIENT_CONNECT
    CLIENT_DISCONNECT

    PING
    JOIN
    PART
    PRIVMSG
    NOTICE
    RPL_WELCOME (001)
    RPL_YOURHOST (002)
    RPL_CREATED (003)
    RPL_MYINFO (004)
    RPL_BOUNCE (005)
    RPL_MOTDSTART (375)
    RPL_MOTD (372)
    RPL_ENDOFMOTD (376)
    RPL_LUSERCLIENT (251)
    RPL_LUSERME (255)
    RPL_LUSEROP (252)
    RPL_LUSERUNKNOWN (253)
    RPL_LUSERCHANNELS (254)
