Commands
^^^^^^^^

.. code-block:: python

    client.send('PASS', password='hunter2')

.. code-block:: python

    client.send('NICK', nick='WiZ')

.. code-block:: python

    # mode is optional, default is 0
    client.send('USER', user='WiZ-user', realname='Ronnie')
    client.send('USER', user='WiZ-user', mode='8', realname='Ronnie')

.. code-block:: python

    client.send('OPER', user='WiZ', password='hunter2')

.. code-block:: python

    # Renamed from MODE
    client.send('USERMODE', nick='WiZ')
    client.send('USERMODE', nick='WiZ', modes='+io')

.. code-block:: python

    client.send('SERVICE', nick='CHANSERV', distribution='*.en',
                type='0', info='manages channels')

.. code-block:: python

    client.send('QUIT')
    client.send('QUIT', message='Gone to Lunch')

.. code-block:: python

    client.send('SQUIT', server='tolsun.oulu.fi')
    client.send('SQUIT', server='tolsun.oulu.fi', message='Bad Link')

.. code-block:: python

    # If channel has n > 1 values, key MUST have 1 or n values
    client.send('JOIN', channel='0')  # send PART to all joined channels
    client.send('JOIN', channel='#foo-chan')
    client.send('JOIN', channel='#foo-chan', key='foo-key')
    client.send('JOIN', channel=['#foo-chan', '#other'],
                key='key-for-both')
    client.send('JOIN', channel=['#foo-chan', '#other'],
                key=['foo-key', 'other-key'])

.. code-block:: python

    client.send('PART', channel='#foo-chan')
    client.send('PART', channel=['#foo-chan', '#other'])
    client.send('PART', channel='#foo-chan', message='I lost')

.. code-block:: python

    # Renamed from MODE
    client.send('CHANNELMODE', channel='#foo-chan', modes='+b')
    client.send('CHANNELMODE', channel='#foo-chan', modes='+l',
                params='10')

.. code-block:: python

    client.send('TOPIC', channel='#foo-chan')
    client.send('TOPIC', channel='#foo-chan',  # Clear channel message
                message='')
    client.send('TOPIC', channel='#foo-chan',
                message='Yes, this is dog')

.. code-block:: python

    # target requires channel
    client.send('NAMES')
    client.send('NAMES', channel='#foo-chan')
    client.send('NAMES', channel=['#foo-chan', '#other'])
    client.send('NAMES', channel=['#foo-chan', '#other'],
                target='remote.*.edu')

.. code-block:: python

    # target requires channel
    client.send('LIST')
    client.send('LIST', channel='#foo-chan')
    client.send('LIST', channel=['#foo-chan', '#other'])
    client.send('LIST', channel=['#foo-chan', '#other'],
                target='remote.*.edu')

.. code-block:: python

    client.send('INVITE', nick='WiZ-friend', channel='#bar-chan')

.. code-block:: python

    # nick and channel must have the same number of elements
    client.send('KICK', channel='#foo-chan', nick='WiZ')
    client.send('KICK', channel='#foo-chan', nick='WiZ',
                message='Spamming')
    client.send('KICK', channel='#foo-chan', nick=['WiZ', 'WiZ-friend'])
    client.send('KICK', channel=['#foo', '#bar'],
                nick=['WiZ', 'WiZ-friend'])

.. code-block:: python

    client.send('PRIVMSG', target='WiZ-friend', message='Hello, friend!')

.. code-block:: python

    client.send('NOTICE', target='#foo-chan',
                message='Maintenance in 5 mins')

.. code-block:: python

    client.send('MOTD')
    client.send('MOTD', target='remote.*.edu')

.. code-block:: python

    client.send('LUSERS')
    client.send('LUSERS', mask='*.edu')
    client.send('LUSERS', mask='*.edu', target='remote.*.edu')

.. code-block:: python

    client.send('VERSION')

.. code-block:: python

    # target requires query
    client.send('STATS')
    client.send('STATS', query='m')
    client.send('STATS', query='m', target='remote.*.edu')

.. code-block:: python

    # remote requires mask
    client.send('LINKS')
    client.send('LINKS', mask='*.bu.edu')
    client.send('LINKS', remote='*.edu', mask='*.bu.edu')

.. code-block:: python

    client.send('TIME')
    client.send('TIME', target='remote.*.edu')

.. code-block:: python

    client.send('CONNECT', target='tolsun.oulu.fi', port=6667)
    client.send('CONNECT', target='tolsun.oulu.fi', port=6667,
                remote='*.edu')

.. code-block:: python

    client.send('TRACE')
    client.send('TRACE', target='remote.*.edu')

.. code-block:: python

    client.send('ADMIN')
    client.send('ADMIN', target='remote.*.edu')

.. code-block:: python

    client.send('INFO')
    client.send('INFO', target='remote.*.edu')

.. code-block:: python

    # type requires mask
    client.send('SERVLIST', mask='*SERV')
    client.send('SERVLIST', mask='*SERV', type=3)

.. code-block:: python

    client.send('SQUERY', target='irchelp', message='HELP privmsg')

.. code-block:: python

    client.send('WHO')
    client.send('WHO', mask='*.fi')
    client.send('WHO', mask='*.fi', o=True)

.. code-block:: python

    client.send('WHOIS', mask='*.fi')
    client.send('WHOIS', mask=['*.fi', '*.edu'], target='remote.*.edu')

.. code-block:: python

    # target requires count
    client.send('WHOWAS', nick='WiZ')
    client.send('WHOWAS', nick='WiZ', count=10)
    client.send('WHOWAS', nick=['WiZ', 'WiZ-friend'], count=10)
    client.send('WHOWAS', nick='WiZ', count=10, target='remote.*.edu')

.. code-block:: python

    client.send('KILL', nick='WiZ', message='Spamming Joins')

.. code-block:: python

    # server2 requires server1
    client.send('PING', message='Test..')
    client.send('PING', server2='tolsun.oulu.fi')
    client.send('PING', server1='WiZ', server2='tolsun.oulu.fi')

.. code-block:: python

    # server2 requires server1
    client.send('PONG', message='Test..')
    client.send('PONG', server2='tolsun.oulu.fi')
    client.send('PONG', server1='WiZ', server2='tolsun.oulu.fi')

.. code-block:: python

    client.send('AWAY')
    client.send('AWAY', message='Gone to Lunch')

.. code-block:: python

    client.send('REHASH')

.. code-block:: python

    client.send('DIE')

.. code-block:: python

    client.send('RESTART')

.. code-block:: python

    # target requires channel
    client.send('SUMMON', nick='WiZ')
    client.send('SUMMON', nick='WiZ', target='remote.*.edu')
    client.send('SUMMON', nick='WiZ', target='remote.*.edu',
                channel='#foo-chan')

.. code-block:: python

    client.send('USERS')
    client.send('USERS', target='remote.*.edu')

.. code-block:: python

    client.send('WALLOPS', message='Maintenance in 5 minutes')

.. code-block:: python

    client.send('USERHOST', nick='WiZ')
    client.send('USERHOST', nick=['WiZ', 'WiZ-friend'])

.. code-block:: python

    client.send('ISON', nick='WiZ')
    client.send('ISON', nick=['WiZ', 'WiZ-friend'])
