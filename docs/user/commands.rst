RFC2812 Support
^^^^^^^^^^^^^^^

.. _Commands:

Sending IRC Commands
====================

.. code-block:: python

    await client.send('PASS', password='hunter2')

.. code-block:: python

    await client.send('NICK', nick='WiZ')

.. code-block:: python

    # mode is optional, default is 0
    await client.send('USER', user='WiZ-user', realname='Ronnie')
    await client.send('USER', user='WiZ-user', mode='8', realname='Ronnie')

.. code-block:: python

    await client.send('OPER', user='WiZ', password='hunter2')

.. code-block:: python

    # Renamed from MODE
    await client.send('USERMODE', nick='WiZ')
    await client.send('USERMODE', nick='WiZ', modes='+io')

.. code-block:: python

    await client.send('SERVICE', nick='CHANSERV', distribution='*.en',
                type='0', info='manages channels')

.. code-block:: python

    await client.send('QUIT')
    await client.send('QUIT', message='Gone to Lunch')

.. code-block:: python

    await client.send('SQUIT', server='tolsun.oulu.fi')
    await client.send('SQUIT', server='tolsun.oulu.fi', message='Bad Link')

.. code-block:: python

    await client.send('JOIN', channel='#foo-chan')
    await client.send('JOIN', channel='#foo-chan', key='foo-key')
    await client.send('JOIN', channel=['#foo-chan', '#other'],
                key='foo-key') # other has no key
    await client.send('JOIN', channel=['#foo-chan', '#other'],
                key=['foo-key', 'other-key'])

    # this will cause you to LEAVE all currently joined channels
    await client.send('JOIN', channel='0')

.. code-block:: python

    await client.send('PART', channel='#foo-chan')
    await client.send('PART', channel=['#foo-chan', '#other'])
    await client.send('PART', channel='#foo-chan', message='I lost')

.. code-block:: python

    # Renamed from MODE
    await client.send('CHANNELMODE', channel='#foo-chan', modes='+b')
    await client.send('CHANNELMODE', channel='#foo-chan', modes='+l',
                params='10')

.. code-block:: python

    await client.send('TOPIC', channel='#foo-chan')
    await client.send('TOPIC', channel='#foo-chan',  # Clear channel message
                message='')
    await client.send('TOPIC', channel='#foo-chan',
                message='Yes, this is dog')

.. code-block:: python

    # target requires channel
    await client.send('NAMES')
    await client.send('NAMES', channel='#foo-chan')
    await client.send('NAMES', channel=['#foo-chan', '#other'])
    await client.send('NAMES', channel=['#foo-chan', '#other'],
                target='remote.*.edu')

.. code-block:: python

    # target requires channel
    await client.send('LIST')
    await client.send('LIST', channel='#foo-chan')
    await client.send('LIST', channel=['#foo-chan', '#other'])
    await client.send('LIST', channel=['#foo-chan', '#other'],
                target='remote.*.edu')

.. code-block:: python

    await client.send('INVITE', nick='WiZ-friend', channel='#bar-chan')

.. code-block:: python

    # nick and channel must have the same number of elements
    await client.send('KICK', channel='#foo-chan', nick='WiZ')
    await client.send('KICK', channel='#foo-chan', nick='WiZ',
                message='Spamming')
    await client.send('KICK', channel='#foo-chan', nick=['WiZ', 'WiZ-friend'])
    await client.send('KICK', channel=['#foo', '#bar'],
                nick=['WiZ', 'WiZ-friend'])

.. code-block:: python

    await client.send('PRIVMSG', target='WiZ-friend', message='Hello, friend!')

.. code-block:: python

    await client.send('NOTICE', target='#foo-chan',
                message='Maintenance in 5 mins')

.. code-block:: python

    await client.send('MOTD')
    await client.send('MOTD', target='remote.*.edu')

.. code-block:: python

    await client.send('LUSERS')
    await client.send('LUSERS', mask='*.edu')
    await client.send('LUSERS', mask='*.edu', target='remote.*.edu')

.. code-block:: python

    await client.send('VERSION')

.. code-block:: python

    # target requires query
    await client.send('STATS')
    await client.send('STATS', query='m')
    await client.send('STATS', query='m', target='remote.*.edu')

.. code-block:: python

    # remote requires mask
    await client.send('LINKS')
    await client.send('LINKS', mask='*.bu.edu')
    await client.send('LINKS', mask='*.bu.edu', remote='*.edu')

.. code-block:: python

    await client.send('TIME')
    await client.send('TIME', target='remote.*.edu')

.. code-block:: python

    await client.send('CONNECT', target='tolsun.oulu.fi', port=6667)
    await client.send('CONNECT', target='tolsun.oulu.fi', port=6667,
                remote='*.edu')

.. code-block:: python

    await client.send('TRACE')
    await client.send('TRACE', target='remote.*.edu')

.. code-block:: python

    await client.send('ADMIN')
    await client.send('ADMIN', target='remote.*.edu')

.. code-block:: python

    await client.send('INFO')
    await client.send('INFO', target='remote.*.edu')

.. code-block:: python

    # type requires mask
    await client.send('SERVLIST', mask='*SERV')
    await client.send('SERVLIST', mask='*SERV', type=3)

.. code-block:: python

    await client.send('SQUERY', target='irchelp', message='HELP privmsg')

.. code-block:: python

    await client.send('WHO')
    await client.send('WHO', mask='*.fi')
    await client.send('WHO', mask='*.fi', o=True)

.. code-block:: python

    await client.send('WHOIS', mask='*.fi')
    await client.send('WHOIS', mask=['*.fi', '*.edu'], target='remote.*.edu')

.. code-block:: python

    # target requires count
    await client.send('WHOWAS', nick='WiZ')
    await client.send('WHOWAS', nick='WiZ', count=10)
    await client.send('WHOWAS', nick=['WiZ', 'WiZ-friend'], count=10)
    await client.send('WHOWAS', nick='WiZ', count=10, target='remote.*.edu')

.. code-block:: python

    await client.send('KILL', nick='WiZ', message='Spamming Joins')

.. code-block:: python

    # PING the server you are connected to
    await client.send('PING')
    await client.send('PING', message='Test..')

.. code-block:: python

    # when replying to a PING, the message should be the same
    await client.send('PONG')
    await client.send('PONG', message='Test..')

.. code-block:: python

    await client.send('AWAY')
    await client.send('AWAY', message='Gone to Lunch')

.. code-block:: python

    await client.send('REHASH')

.. code-block:: python

    await client.send('DIE')

.. code-block:: python

    await client.send('RESTART')

.. code-block:: python

    # target requires channel
    await client.send('SUMMON', nick='WiZ')
    await client.send('SUMMON', nick='WiZ', target='remote.*.edu')
    await client.send('SUMMON', nick='WiZ', target='remote.*.edu',
                channel='#foo-chan')

.. code-block:: python

    await client.send('USERS')
    await client.send('USERS', target='remote.*.edu')

.. code-block:: python

    await client.send('WALLOPS', message='Maintenance in 5 minutes')

.. code-block:: python

    await client.send('USERHOST', nick='WiZ')
    await client.send('USERHOST', nick=['WiZ', 'WiZ-friend'])

.. code-block:: python

    await client.send('ISON', nick='WiZ')
    await client.send('ISON', nick=['WiZ', 'WiZ-friend'])


.. _Events:

Receiving IRC Events
====================

.. code-block:: python

    # Local only events
    client.trigger('CLIENT_CONNECT')
    client.trigger('CLIENT_DISCONNECT')

* PING
* JOIN
* PART
* PRIVMSG
* NOTICE
* USERMODE (renamed from MODE)
* CHANNELMODE (renamed from MODE)
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
* ERR_NOMOTD (422)
