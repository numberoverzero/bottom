""" Simplified support for rfc2812 """
# https://tools.ietf.org/html/rfc2812
import collections
MISSING = object()


def b(field, kwargs, present=MISSING, missing=''):
    '''
    Return `present` value (default to `field`) if `field` in `kwargs` and
    Truthy, otherwise return `missing` value
    '''
    if bool(kwargs.get(field, False)):
        return field if present is MISSING else str(present)
    return str(missing)


def f(field, kwargs, default=MISSING):
    ''' Alias for more readable command construction '''
    if default is not MISSING:
        return str(kwargs.get(field, default))
    return str(kwargs[field])


def pack(field, kwargs, default=MISSING, sep=","):
    ''' Util for joining multiple fields with commas '''
    if default is not MISSING:
        value = kwargs.get(field, default)
    else:
        value = kwargs[field]
    if isinstance(value, str):
        return value
    elif isinstance(value, collections.abc.Iterable):
        return sep.join(str(f) for f in value)
    else:
        return str(value)


def pack_command(command, **kwargs):
    """ Pack a command to send to an IRC server """
    if not command:
        raise ValueError("Must provide a command")
    try:
        command = command.upper()
    except AttributeError:
        raise ValueError("Command must be a str")

    # ========================================================================
    # For each command, provide:
    #  1. a link to the definition in rfc2812
    #  2. the normalized grammar, which may not equate to the rfc grammar
    #     the normalized grammar will use the keys expected in kwargs,
    #     which usually do NOT line up with rfc2812.  They may also make
    #     optional fields which are required in rfc2812, by providing
    #     the most common or reasonable defaults.
    #  3. exhaustive examples, preferring normalized form of
    #     the rfc2812 examples
    # ========================================================================

    # ========================================================================
    # Normalized grammar:
    # : should not be provided; it denotes the beginning of the last
    #   field, which may contain spaces
    # [] indicates an optional field
    # <> denote the key that the field will be filled with
    # because fields are filled from a dict, required fields may follow
    #   optional fields - see USER command, where mode is optional
    #   (and defaults to 0)
    # "" indicates a literal value that is inserted if present
    # ========================================================================

    # PASS
    # https://tools.ietf.org/html/rfc2812#section-3.1.1
    # PASS <password>
    # ----------
    # PASS secretpasswordhere
    if command == "PASS":
        return "PASS " + f("password", kwargs)

    # NICK
    # https://tools.ietf.org/html/rfc2812#section-3.1.2
    # NICK <nick>
    # ----------
    # NICK Wiz
    elif command == "NICK":
        return "NICK " + f("nick", kwargs)

    # USER
    # https://tools.ietf.org/html/rfc2812#section-3.1.3
    # USER <user> [<mode>] :<realname>
    # ----------
    # USER guest 8 :Ronnie Reagan
    # USER guest :Ronnie Reagan
    elif command == "USER":
        return "USER {} {} * :{}".format(
            f("user", kwargs),
            f("mode", kwargs, 0),
            f("realname", kwargs))

    # OPER
    # https://tools.ietf.org/html/rfc2812#section-3.1.4
    # OPER <user> <password>
    # ----------
    # OPER AzureDiamond hunter2
    elif command == "OPER":
        return "OPER {} {}".format(f("user", kwargs), f("password", kwargs))

    # USERMODE (renamed from MODE)
    # https://tools.ietf.org/html/rfc2812#section-3.1.5
    # MODE <nick> [<modes>]
    # ----------
    # MODE WiZ -w
    # MODE Angel +i
    # MODE
    elif command == "USERMODE":
        return "MODE {} {}".format(f("nick", kwargs), f("modes", kwargs, ''))

    # SERVICE
    # https://tools.ietf.org/html/rfc2812#section-3.1.6
    # SERVICE <nick> <distribution> <type> :<info>
    # ----------
    # SERVICE dict *.fr 0 :French
    elif command == "SERVICE":
        return "SERVICE {} * {} {} 0 :{}".format(
            f("nick", kwargs),
            f("distribution", kwargs),
            f("type", kwargs),
            f("info", kwargs))

    # QUIT
    # https://tools.ietf.org/html/rfc2812#section-3.1.7
    # QUIT :[<message>]
    # ----------
    # QUIT :Gone to lunch
    # QUIT
    elif command == "QUIT":
        if "message" in kwargs:
            return "QUIT :" + f("message", kwargs)
        return "QUIT"

    # SQUIT
    # https://tools.ietf.org/html/rfc2812#section-3.1.8
    # SQUIT <server> [<message>]
    # ----------
    # SQUIT tolsun.oulu.fi :Bad Link
    # SQUIT tolsun.oulu.fi
    elif command == "SQUIT":
        base = "SQUIT " + f("server", kwargs)
        if "message" in kwargs:
            return base + " :" + f("message", kwargs)
        return base

    # JOIN
    # https://tools.ietf.org/html/rfc2812#section-3.2.1
    # JOIN <channel> [<key>]
    # ----------
    # JOIN #foo fookey
    # JOIN #foo
    # JOIN 0
    elif command == "JOIN":
        return "JOIN {} {}".format(pack("channel", kwargs),
                                   pack("key", kwargs, ''))

    # PART
    # https://tools.ietf.org/html/rfc2812#section-3.2.2
    # PART <channel> :[<message>]
    # ----------
    # PART #foo :I lost
    # PART #foo
    elif command == "PART":
        base = "PART " + pack("channel", kwargs)
        if "message" in kwargs:
            return base + " :" + f("message", kwargs)
        return base

    # CHANNELMODE (renamed from MODE)
    # https://tools.ietf.org/html/rfc2812#section-3.2.3
    # MODE <channel> <modes> [<params>]
    # ----------
    # MODE #Finnish +imI *!*@*.fi
    # MODE #en-ops +v WiZ
    # MODE #Fins -s
    elif command == "CHANNELMODE":
        return "MODE {} {} {}".format(f("channel", kwargs),
                                      f("modes", kwargs),
                                      f("params", kwargs, ''))

    # TOPIC
    # https://tools.ietf.org/html/rfc2812#section-3.2.4
    # TOPIC <channel> :[<message>]
    # ----------
    # TOPIC #test :New topic
    # TOPIC #test :
    # TOPIC #test
    elif command == "TOPIC":
        base = "TOPIC " + f("channel", kwargs)
        if "message" in kwargs:
            return base + " :" + f("message", kwargs)
        return base

    # NAMES
    # https://tools.ietf.org/html/rfc2812#section-3.2.5
    # NAMES [<channel>] [<target>]
    # ----------
    # NAMES #twilight_zone remote.*.edu
    # NAMES #twilight_zone
    # NAMES
    elif command == "NAMES":
        if "channel" in kwargs:
            return "NAMES {} {}".format(pack("channel", kwargs),
                                        f("target", kwargs, ''))
        return "NAMES"

    # LIST
    # https://tools.ietf.org/html/rfc2812#section-3.2.6
    # LIST [<channel>] [<target>]
    # ----------
    # LIST #twilight_zone remote.*.edu
    # LIST #twilight_zone
    # LIST
    elif command == "LIST":
        if "channel" in kwargs:
            return "LIST {} {}".format(pack("channel", kwargs),
                                       f("target", kwargs, ''))
        return "LIST"

    # INVITE
    # https://tools.ietf.org/html/rfc2812#section-3.2.7
    # INVITE <nick> <channel>
    # ----------
    # INVITE Wiz #Twilight_Zone
    elif command == "INVITE":
        return "INVITE {} {}".format(f("nick", kwargs),
                                     f("channel", kwargs))

    # KICK
    # https://tools.ietf.org/html/rfc2812#section-3.2.8
    # KICK <channel> <nick> :[<message>]
    # ----------
    # KICK #Finnish WiZ :Speaking English
    # KICK #Finnish WiZ,Wiz-Bot :Both speaking English
    # KICK #Finnish,#English WiZ,ZiW :Speaking wrong language
    elif command == "KICK":
        base = "KICK {} {}".format(pack("channel", kwargs),
                                   pack("nick", kwargs))
        if "message" in kwargs:
            return base + " :" + pack("message", kwargs)
        return base

    # PRIVMSG
    # https://tools.ietf.org/html/rfc2812#section-3.3.1
    # PRIVMSG <target> :<message>
    # ----------
    # PRIVMSG Angel :yes I'm receiving it !
    # PRIVMSG $*.fi :Server tolsun.oulu.fi rebooting.
    # PRIVMSG #Finnish :This message is in english
    elif command == "PRIVMSG":
        return "PRIVMSG {} :{}".format(f("target", kwargs),
                                       f("message", kwargs))

    # NOTICE
    # https://tools.ietf.org/html/rfc2812#section-3.3.2
    # NOTICE <target> :<message>
    # ----------
    # NOTICE Angel :yes I'm receiving it !
    # NOTICE $*.fi :Server tolsun.oulu.fi rebooting.
    # NOTICE #Finnish :This message is in english
    elif command == "NOTICE":
        return "NOTICE {} :{}".format(f("target", kwargs),
                                      f("message", kwargs))

    # MOTD
    # https://tools.ietf.org/html/rfc2812#section-3.4.1
    # MOTD [<target>]
    # ----------
    # MOTD remote.*.edu
    # MOTD
    elif command == "MOTD":
        return "MOTD " + f("target", kwargs, '')

    # LUSERS
    # https://tools.ietf.org/html/rfc2812#section-3.4.2
    # LUSERS [<mask>] [<target>]
    # ----------
    # LUSERS *.edu remote.*.edu
    # LUSERS *.edu
    # LUSERS
    elif command == "LUSERS":
        if "mask" in kwargs:
            return "LUSERS {} {}".format(f("mask", kwargs),
                                         f("target", kwargs, ''))
        return "LUSERS"

    # VERSION
    # https://tools.ietf.org/html/rfc2812#section-3.4.3
    # VERSION [<target>]
    # ----------
    # VERSION remote.*.edu
    # VERSION
    elif command == "VERSION":
        return "VERSION " + f("target", kwargs, '')

    # STATS
    # https://tools.ietf.org/html/rfc2812#section-3.4.4
    # STATS [<query>] [<target>]
    # ----------
    # STATS m remote.*.edu
    # STATS m
    # STATS
    elif command == "STATS":
        if "query" in kwargs:
            return "STATS {} {}".format(f("query", kwargs),
                                        f("target", kwargs, ''))
        return "STATS"

    # LINKS
    # https://tools.ietf.org/html/rfc2812#section-3.4.5
    # LINKS [<remote>] [<mask>]
    # ----------
    # LINKS *.edu *.bu.edu
    # LINKS *.au
    # LINKS
    elif command == "LINKS":
        if "remote" in kwargs:
            return "LINKS {} {}".format(f("remote", kwargs), f("mask", kwargs))
        elif "mask" in kwargs:
            return "LINKS " + f("mask", kwargs)
        return "LINKS"

    # TIME
    # https://tools.ietf.org/html/rfc2812#section-3.4.6
    # TIME [<target>]
    # ----------
    # TIME remote.*.edu
    # TIME
    elif command == "TIME":
        return "TIME " + f("target", kwargs, '')

    # CONNECT
    # https://tools.ietf.org/html/rfc2812#section-3.4.7
    # CONNECT <target> <port> [<remote>]
    # ----------
    # CONNECT tolsun.oulu.fi 6667 *.edu
    # CONNECT tolsun.oulu.fi 6667
    elif command == "CONNECT":
        return "CONNECT {} {} {}".format(f("target", kwargs),
                                         f("port", kwargs),
                                         f("remote", kwargs, ''))

    # TRACE
    # https://tools.ietf.org/html/rfc2812#section-3.4.8
    # TRACE [<target>]
    # ----------
    # TRACE
    elif command == "TRACE":
        return "TRACE " + f("target", kwargs, '')

    # ADMIN
    # https://tools.ietf.org/html/rfc2812#section-3.4.9
    # ADMIN [<target>]
    # ----------
    # ADMIN
    elif command == "ADMIN":
        return "ADMIN " + f("target", kwargs, '')

    # INFO
    # https://tools.ietf.org/html/rfc2812#section-3.4.10
    # INFO [<target>]
    # ----------
    # INFO
    elif command == "INFO":
        return "INFO " + f("target", kwargs, '')

    # SERVLIST
    # https://tools.ietf.org/html/rfc2812#section-3.5.1
    # SERVLIST [<mask>] [<type>]
    # ----------
    # SERVLIST *SERV 3
    # SERVLIST *SERV
    # SERVLIST
    elif command == "SERVLIST":
        return "SERVLIST {} {}".format(f("mask", kwargs, ''),
                                       f("type", kwargs, ''))

    # SQUERY
    # https://tools.ietf.org/html/rfc2812#section-3.5.2
    # SQUERY <target> :<message>
    # ----------
    # SQUERY irchelp :HELP privmsg
    elif command == "SQUERY":
        return "SQUERY {} :{}".format(f("target", kwargs),
                                      f("message", kwargs))

    # WHO
    # https://tools.ietf.org/html/rfc2812#section-3.6.1
    # WHO [<mask>] ["o"]
    # ----------
    # WHO jto* o
    # WHO *.fi
    # WHO
    elif command == "WHO":
        return "WHO {} {}".format(f("mask", kwargs, ''), b("o", kwargs))

    # WHOIS
    # https://tools.ietf.org/html/rfc2812#section-3.6.2
    # WHOIS <mask> [<target>]
    # ----------
    # WHOIS jto* o remote.*.edu
    # WHOIS jto* o
    # WHOIS *.fi
    elif command == "WHOIS":
        return "WHOIS {} {}".format(pack("mask", kwargs),
                                    f("target", kwargs, ''))

    # WHOWAS
    # https://tools.ietf.org/html/rfc2812#section-3.6.3
    # WHOWAS <nick> [<count>] [<target>]
    # ----------
    # WHOWAS Wiz 9 remote.*.edu
    # WHOWAS Wiz 9
    # WHOWAS Mermaid
    elif command == "WHOWAS":
        if "count" in kwargs:
            return "WHOWAS {} {} {}".format(pack("nick", kwargs),
                                            f("count", kwargs),
                                            f("target", kwargs, ''))
        return "WHOWAS " + pack("nick", kwargs)

    # KILL
    # https://tools.ietf.org/html/rfc2812#section-3.7.1
    # KILL <nick> :<message>
    # ----------
    # KILL WiZ :Spamming joins
    elif command == "KILL":
        return "KILL {} :{}".format(f("nick", kwargs), f("message", kwargs))

    # PING
    # https://tools.ietf.org/html/rfc2812#section-3.7.3
    # PING [<server1>] [<server2>] :[<message>]
    # ----------
    # PING csd.bu.edu tolsun.oulu.fi :Keepalive
    # PING csd.bu.edu :I'm still here
    # PING :I'm still here
    # PING
    elif command == "PING":
        message = "PING {} {}".format(f("server1", kwargs, ''),
                                      f("server2", kwargs, ''))
        if "message" in kwargs:
            message += " :" + f("message", kwargs)
        return message

    # PONG
    # https://tools.ietf.org/html/rfc2812#section-3.7.3
    # PONG [<server1>] [<server2>] :[<message>]
    # ----------
    # PONG csd.bu.edu tolsun.oulu.fi :Keepalive
    # PONG csd.bu.edu :I'm still here
    # PONG :I'm still here
    # PONG
    elif command == "PONG":
        message = "PONG {} {}".format(f("server1", kwargs, ''),
                                      f("server2", kwargs, ''))
        if "message" in kwargs:
            message += " :" + f("message", kwargs)
        return message

    # AWAY
    # https://tools.ietf.org/html/rfc2812#section-4.1
    # AWAY :[<message>]
    # ----------
    # AWAY :Gone to lunch.
    # AWAY
    elif command == "AWAY":
        if "message" in kwargs:
            return "AWAY :" + f("message", kwargs)
        return "AWAY"

    # REHASH
    # https://tools.ietf.org/html/rfc2812#section-4.2
    # REHASH
    # ----------
    # REHASH
    elif command == "REHASH":
        return "REHASH"

    # DIE
    # https://tools.ietf.org/html/rfc2812#section-4.3
    # DIE
    # ----------
    # DIE
    elif command == "DIE":
        return "DIE"

    # RESTART
    # https://tools.ietf.org/html/rfc2812#section-4.4
    # RESTART
    # ----------
    # RESTART
    elif command == "RESTART":
        return "RESTART"

    # SUMMON
    # https://tools.ietf.org/html/rfc2812#section-4.5
    # SUMMON <nick> [<target>] [<channel>]
    # ----------
    # SUMMON Wiz remote.*.edu #Finnish
    # SUMMON Wiz remote.*.edu
    # SUMMON Wiz
    elif command == "SUMMON":
        if "target" in kwargs:
            return "SUMMON {} {} {}".format(f("nick", kwargs),
                                            f("target", kwargs),
                                            f("channel", kwargs, ''))
        return "SUMMON " + f("nick", kwargs)

    # USERS
    # https://tools.ietf.org/html/rfc2812#section-4.6
    # USERS [<target>]
    # ----------
    # USERS remote.*.edu
    # USERS
    elif command == "USERS":
        return "USERS " + f("target", kwargs, '')

    # WALLOPS
    # https://tools.ietf.org/html/rfc2812#section-4.7
    # WALLOPS :<message>
    # ----------
    # WALLOPS :Maintenance in 5 minutes
    elif command == "WALLOPS":
        return "WALLOPS :" + f("message", kwargs)

    # USERHOST
    # https://tools.ietf.org/html/rfc2812#section-4.8
    # USERHOST <nick>
    # ----------
    # USERHOST Wiz Michael syrk
    # USERHOST syrk
    elif command == "USERHOST":
        return "USERHOST " + pack("nick", kwargs, sep=" ")

    # ISON
    # https://tools.ietf.org/html/rfc2812#section-4.9
    # ISON <nick>
    # ----------
    # ISON Wiz Michael syrk
    # ISON syrk
    elif command == "ISON":
        return "ISON " + pack("nick", kwargs, sep=" ")

    else:
        raise ValueError("Unknown command '{}'".format(command))
