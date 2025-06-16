Built-in Commands and Events
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _Commands:

Sending IRC Commands
====================

The global default :class:`serializer<bottom.CommandSerializer>` includes 45 commands from
`rfc2812<https://datatracker.ietf.org/doc/html/rfc2812>`.  You can :ref:`extend this<ex-serialize>` with your own
commands.  The client's :meth:`@Client.on<bottom.Client.on>` method includes type overloads for the built-in commands.
Finally, you can use the script ``bin/print-commands.py`` (copied below) to print a client's known commands::

    from bottom import Client

    def help_known_commands(client: Client) -> str:
        out = []
        all_templates = client._serializer.templates
        for command in sorted(all_templates.keys()):
            out.append(command)
            for tpl in all_templates[command]:
                out.append(f"  {tpl.original}")
        return "\n".join(out)


    my_client = Client("localhost", 6697)
    print(help_known_commands(my_client))


GLOBAL_SERIALIZER default commands
----------------------------------

*(note: generated with the previous command)*

.. code-block:: text

  ADMIN
    ADMIN {target}
    ADMIN

  AWAY
    AWAY :{message}
    AWAY

  CHANNELMODE
    MODE {channel} {params:space}

  CONNECT
    CONNECT {target} {port} {remote}
    CONNECT {target} {port}

  DIE
    DIE

  INFO
    INFO {target}
    INFO

  INVITE
    INVITE {nick} {channel}

  ISON
    ISON {nick:space}

  JOIN
    JOIN {channel:comma} {key:comma}
    JOIN {channel:comma}

  KICK
    KICK {channel:comma} {nick:comma} :{message}
    KICK {channel:comma} {nick:comma}

  KILL
    KILL {nick} :{message}

  LINKS
    LINKS {remote} {mask}
    LINKS {mask}
    LINKS

  LIST
    LIST {channel:comma} {target}
    LIST {channel:comma}
    LIST

  LUSERS
    LUSERS {mask} {target}
    LUSERS {mask}
    LUSERS

  MOTD
    MOTD {target}
    MOTD

  NAMES
    NAMES {channel:comma} {target}
    NAMES {channel:comma}
    NAMES

  NICK
    NICK {nick}

  NOTICE
    NOTICE {target} :{message}

  OPER
    OPER {nick} {password}

  PART
    PART {channel:comma} :{message}
    PART {channel:comma}

  PASS
    PASS {password}

  PING
    PING {message:nospace} {target}
    PING {message:nospace}

  PONG
    PONG :{message}
    PONG

  PRIVMSG
    PRIVMSG {target} :{message}

  QUIT
    QUIT :{message}
    QUIT

  REHASH
    REHASH

  RESTART
    RESTART

  SERVICE
    SERVICE {nick} * {distribution} {type} 0 :{info}

  SERVLIST
    SERVLIST {mask} {type}
    SERVLIST {mask}
    SERVLIST

  SQUERY
    SQUERY {target} :{message}

  SQUIT
    SQUIT {server} :{message}
    SQUIT {server}

  STATS
    STATS {query} {target}
    STATS {query}
    STATS

  SUMMON
    SUMMON {nick} {target} {channel}
    SUMMON {nick} {target}
    SUMMON {nick}

  TIME
    TIME {target}
    TIME

  TOPIC
    TOPIC {channel} :{message}
    TOPIC {channel}

  TRACE
    TRACE {target}
    TRACE

  USER
    USER {nick} {mode} * :{realname}
    USER {nick} 0 * :{realname}

  USERHOST
    USERHOST {nick:space}

  USERMODE
    MODE {nick} {modes}
    MODE {nick}

  USERS
    USERS {target}
    USERS

  VERSION
    VERSION {target}
    VERSION

  WALLOPS
    WALLOPS :{message}

  WHO
    WHO {mask} {o:bool}
    WHO {mask}
    WHO

  WHOIS
    WHOIS {target} {mask:comma}
    WHOIS {mask:comma}

  WHOWAS
    WHOWAS {nick:comma} {count} {target}
    WHOWAS {nick:comma} {count}
    WHOWAS {nick:comma}



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
