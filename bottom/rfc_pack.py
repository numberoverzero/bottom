""" Simplified support for rfc2812 """
# http://tools.ietf.org/html/rfc2812
import collections
missing = object()


def f(field, kwargs, default=missing):
    ''' Alias for more readable command construction '''
    if default is not missing:
        return str(kwargs.get(field, default))
    return str(kwargs[field])


def pack(field, kwargs, default=missing, sep=","):
    ''' Util for joining multiple fields with commas '''
    if default is not missing:
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
    # Diversions from rfc2812
    # For the most part, commands try to stay as close to the spec as
    #   is reasonable.  However, some commands unintuitively overload the
    #   positional arguments, and are inconsistent w.r.t specifying
    #   singular vs multiple values.
    # In those cases, the examples below and normalized grammar will
    #   unambiguously explain how the kwargs dict will be parsed, and
    #   what fields will be used.
    # A list of non-coforming commands and a note on their difference
    #   is kept below for ease of reference.
    #
    # ALL CMDS    RENAMED param FROM <nickname> TO <nick>
    #             RENAMED param FROM <user> TO <nick>
    #                 EXCEPT USER, OPER
    #             RENAMED param FROM <comment> TO <message>
    # ------------------------------------------------------------
    # USER        mode defaults to 0
    # MODE        split into USERMODE and CHANNELMODE.
    #             USERMODE conforms to 3.1.5 User Mode message
    #             CHANNELMODE conforms to 3.
    # USERMODE    (see MODE)
    # QUIT        RENAMED param FROM <Quit Message> TO <message>
    # JOIN        param <channel> can be a list of channels
    #             param <key> can be a list of keys
    # PART        param <channel> can be a list of channels
    # CHANNELMODE (see MODE)
    # TOPIC       RENAMED param FROM <topic> TO <message>
    # NAMES       param <target> is not used.
    #             param <channel> can be a list of channels
    # LIST        param <target> is not used
    #             param <channel> can be a list of channels
    # PRIVMSG     RENAMED param FROM <msgtarget> TO <target>
    #             RENAMED param FROM <text to be sent> TO <message>
    # NOTICE      RENAMED param FROM <msgtarget> TO <target>
    #             RENAMED param FROM <text to be sent> TO <message>
    # MOTD        param <target> is not used.
    # LUSERS      param <target> is not used.
    # VERSION     param <target> is not used.
    # STATS       param <target> is not used.
    # LINKS       RENAMED param FROM <remote server> TO <remote>
    #             RENAMED param FROM <server mask> TO <mask>
    # TIME        param <target> is not used.
    # CONNECT     RENAMED param FROM <target server> TO <target>
    #             RENAMED param FROM <remote server> TO <remote>
    # TRACE       param <target> is not used.
    # ADMIN       param <target> is not used.
    # INFO        param <target> is not used.
    # SQUERY      RENAMED param FROM <servicename> TO <target>
    #             RENAMED param FROM <text> TO <message>
    # WHO         No explicit param for "o" (include in <mask>)
    # WHOIS       param <target> is not used.
    #             param <mask> can be a list of channels
    # WHOWAS      param <target> is not used.
    # PING        NOT IMPLEMENTED
    # PONG        param <server> is not used.
    #             param <server2> is not used.
    #             ADDED optional param <message>
    # ERROR       NOT IMPLEMENTED
    # AWAY        RENAMED param FROM <text> TO <message>
    # SUMMON      param <target> is not used.
    # USERS       param <target> is not used.
    # WALLOPS     RENAMED param FROM <Text to be sent> TO <message>
    # USERHOST    param <nick> can be a list of nicks
    # ISON        param <nick> can be a list of nicks
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
    # ========================================================================

    # PASS
    # http://tools.ietf.org/html/rfc2812#section-3.1.1
    # PASS <password>
    # ----------
    # PASS secretpasswordhere
    if command == "PASS":
        return "PASS " + f("password", kwargs)

    # NICK
    # http://tools.ietf.org/html/rfc2812#section-3.1.2
    # NICK <nick>
    # ----------
    # NICK Wiz
    elif command == "NICK":
        return "NICK " + f("nick", kwargs)

    # USER
    # http://tools.ietf.org/html/rfc2812#section-3.1.3
    # USER <user> [<mode>] <realname>
    # ----------
    # USER guest 8 :Ronnie Reagan
    # USER guest :Ronnie Reagan
    elif command == "USER":
        return "USER {} {} * :{}".format(
            f("user", kwargs),
            f("mode", kwargs, 0),
            f("realname", kwargs))

    # OPER
    # http://tools.ietf.org/html/rfc2812#section-3.1.4
    # OPER <user> <password>
    # ----------
    # OPER AzureDiamond hunter2
    elif command == "OPER":
        return "OPER {} {}".format(f("user", kwargs), f("password", kwargs))

    # USERMODE (renamed from MODE)
    # http://tools.ietf.org/html/rfc2812#section-3.1.5
    # USERMODE <nick> <modes>
    # ----------
    # USERMODE WiZ -w
    # USERMODE Angel +i
    elif command == "USERMODE":
        return "MODE {} {}".format(f("nick", kwargs), f("modes", kwargs))

    # SERVICE
    # http://tools.ietf.org/html/rfc2812#section-3.1.6
    # SERVICE <nick> <distribution> <type> <info>
    # ----------
    # SERVICE dict *.fr 0 :French
    elif command == "SERVICE":
        return "SERVICE {} * {} {} 0 :{}".format(
            f("nick", kwargs),
            f("distribution", kwargs),
            f("type", kwargs),
            f("info", kwargs))

    # QUIT
    # http://tools.ietf.org/html/rfc2812#section-3.1.7
    # QUIT [<message>]
    # ----------
    # QUIT :Gone to lunch
    # QUIT
    elif command == "QUIT":
        if "message" in kwargs:
            return "QUIT :" + f("message", kwargs)
        return "QUIT"

    # SQUIT
    # http://tools.ietf.org/html/rfc2812#section-3.1.8
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
    # http://tools.ietf.org/html/rfc2812#section-3.2.1
    # JOIN <channel> [<key>]
    # ----------
    # JOIN #foo fookey
    # JOIN #foo
    # JOIN 0
    elif command == "JOIN":
        base = "JOIN " + pack("channel", kwargs)
        if "key" in kwargs:
            return base + " " + pack("key", kwargs)
        return base

    # PART
    # http://tools.ietf.org/html/rfc2812#section-3.2.2
    # PART <channel> [<message>]
    # ----------
    # PART #foo :I lost
    # PART #foo
    elif command == "PART":
        base = "PART " + pack("channel", kwargs)
        if "message" in kwargs:
            return base + " :" + f("message", kwargs)
        return base

    # CHANNELMODE (renamed from MODE)
    # http://tools.ietf.org/html/rfc2812#section-3.2.3
    # CHANNELMODE <channel> <modes> [<params>]
    # ----------
    # CHANNELMODE #Finnish +imI *!*@*.fi
    # CHANNELMODE #en-ops +v WiZ
    # CHANNELMODE #Fins -s
    elif command == "CHANNELMODE":
        base = "MODE {} {}".format(f("channel", kwargs), f("modes", kwargs))
        if "params" in kwargs:
            return base + " " + f("params", kwargs)
        return base

    # TOPIC
    # http://tools.ietf.org/html/rfc2812#section-3.2.4
    # TOPIC <channel> [<message>]
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
    # http://tools.ietf.org/html/rfc2812#section-3.2.5
    # NAMES [<channel>]
    # ----------
    # NAMES #twilight_zone
    # NAMES
    elif command == "NAMES":
        if "channel" in kwargs:
            return "NAMES " + pack("channel", kwargs)
        return "NAMES"

    # LIST
    # http://tools.ietf.org/html/rfc2812#section-3.2.6
    # LIST [<channel>]
    # ----------
    # LIST #twilight_zone
    # LIST
    elif command == "LIST":
        if "channel" in kwargs:
            return "LIST " + pack("channel", kwargs)
        return "LIST"

    # INVITE
    # http://tools.ietf.org/html/rfc2812#section-3.2.7
    # INVITE <nick> <channel>
    # ----------
    # INVITE Wiz #Twilight_Zone
    elif command == "INVITE":
        return "INVITE {} {}".format(f("nick", kwargs), f("channel", kwargs))

    # KICK
    # http://tools.ietf.org/html/rfc2812#section-3.2.8
    # KICK <channel> <nick> [<message>]
    # ----------
    # KICK #Finnish WiZ :Speaking English
    # KICK #Finnish WiZ,Wiz-Bot :Both speaking English
    # KICK #Finnish,#English WiZ,ZiW :Speaking wrong language
    elif command == "KICK":
        base = "KICK {} {}".format(
            pack("channel", kwargs), pack("nick", kwargs))
        if "message" in kwargs:
            return base + " :" + pack("message", kwargs)
        return base

    # PRIVMSG
    # http://tools.ietf.org/html/rfc2812#section-3.3.1
    # PRIVMSG <target> <message>
    # ----------
    # PRIVMSG Angel :yes I'm receiving it !
    # PRIVMSG $*.fi :Server tolsun.oulu.fi rebooting.
    # PRIVMSG #Finnish :This message is in english
    elif command == "PRIVMSG":
        return "PRIVMSG {} :{}".format(
            f("target", kwargs), f("message", kwargs))

    # NOTICE
    # http://tools.ietf.org/html/rfc2812#section-3.3.2
    # NOTICE <target> <message>
    # ----------
    # NOTICE Angel :yes I'm receiving it !
    # NOTICE $*.fi :Server tolsun.oulu.fi rebooting.
    # NOTICE #Finnish :This message is in english
    elif command == "NOTICE":
        return "NOTICE {} :{}".format(
            f("target", kwargs), f("message", kwargs))

    # MOTD
    # http://tools.ietf.org/html/rfc2812#section-3.4.1
    # MOTD
    # ----------
    # MOTD
    elif command == "MOTD":
        return "MOTD"

    # LUSERS
    # http://tools.ietf.org/html/rfc2812#section-3.4.2
    # LUSERS [<mask>]
    # ----------
    # LUSERS *.edu
    # LUSERS
    elif command == "LUSERS":
        if "mask" in kwargs:
            return "LUSERS :" + f("mask", kwargs)
        return "LUSERS"

    # VERSION
    # http://tools.ietf.org/html/rfc2812#section-3.4.3
    # VERSION
    # ----------
    # VERSION
    elif command == "VERSION":
        return "VERSION"

    # STATS
    # http://tools.ietf.org/html/rfc2812#section-3.4.4
    # STATS [<query>]
    # ----------
    # STATS m
    # STATS
    elif command == "STATS":
        if "query" in kwargs:
            return "STATS :" + f("query", kwargs)
        return "STATS"

    # LINKS
    # http://tools.ietf.org/html/rfc2812#section-3.4.5
    # LINKS [<remote>] [<mask>]
    # ----------
    # LINKS *.edu *.bu.edu
    # LINKS *.au
    # LINKS
    elif command == "LINKS":
        if "remote" in kwargs:
            return "LINKS {} {}".format(f("remote", kwargs), f("mask", kwargs))
        elif "mask" in kwargs:
            return "LINKS {}" + f("mask", kwargs)
        return "LINKS"

    # TIME
    # http://tools.ietf.org/html/rfc2812#section-3.4.6
    # TIME
    # ----------
    # TIME
    elif command == "TIME":
        return "TIME"

    # CONNECT
    # http://tools.ietf.org/html/rfc2812#section-3.4.7
    # CONNECT <target> <port> [<remote>]
    # ----------
    # CONNECT tolsun.oulu.fi 6667 *.edu
    # CONNECT tolsun.oulu.fi 6667
    elif command == "CONNECT":
        base = "CONNECT {} {}".format(f("target", kwargs), f("port", kwargs))
        if "remote" in kwargs:
            return base + " " + f("remote", kwargs)
        return base

    # TRACE
    # http://tools.ietf.org/html/rfc2812#section-3.4.8
    # TRACE
    # ----------
    # TRACE
    elif command == "TRACE":
        return "TRACE"

    # ADMIN
    # http://tools.ietf.org/html/rfc2812#section-3.4.9
    # ADMIN
    # ----------
    # ADMIN
    elif command == "ADMIN":
        return "ADMIN"

    # INFO
    # http://tools.ietf.org/html/rfc2812#section-3.4.10
    # INFO
    # ----------
    # INFO
    elif command == "INFO":
        return "INFO"

    # SERVLIST
    # http://tools.ietf.org/html/rfc2812#section-3.5.1
    # SERVLIST [<mask>] [<type>]
    # ----------
    # SERVLIST *SERV 3
    # SERVLIST *SERV
    # SERVLIST
    elif command == "SERVLIST":
        if "type" in kwargs:
            return "SERVLIST {} {}".format(
                f("mask", kwargs), f("type", kwargs))
        elif "mask" in kwargs:
            return "SERVLIST {}" + f("mask", kwargs)
        return "SERVLIST"

    # SQUERY
    # http://tools.ietf.org/html/rfc2812#section-3.5.2
    # SQUERY <target> <message>
    # ----------
    # SQUERY irchelp :HELP privmsg
    elif command == "SQUERY":
        return "SQUERY {} :{}".format(
            f("target", kwargs), f("message", kwargs))

    # WHO
    # http://tools.ietf.org/html/rfc2812#section-3.6.1
    # WHO [<mask>]
    # ----------
    # WHO jto* o
    # WHO *.fi
    elif command == "WHO":
        if "mask" in kwargs:
            return "WHO " + f("mask", kwargs)
        return "WHO"

    # WHOIS
    # https://tools.ietf.org/html/rfc2812#section-3.6.2
    # WHOIS <mask>
    # ----------
    # WHOIS jto* o
    # WHOIS *.fi
    elif command == "WHOIS":
        return "WHOIS " + pack("mask", kwargs)

    # WHOWAS
    # https://tools.ietf.org/html/rfc2812#section-3.6.3
    # WHOWAS <nick> [<count>]
    # ----------
    # WHOWAS Wiz 9
    # WHOWAS Mermaid
    elif command == "WHOWAS":
        base = "WHOWAS " + pack("nick", kwargs)
        if "count" in kwargs:
            return base + " " + f("count", kwargs)
        return base

    # KILL
    # https://tools.ietf.org/html/rfc2812#section-3.7.1
    # KILL <nick> <message>
    # ----------
    # KILL WiZ :Spamming joins
    elif command == "KILL":
        return "KILL {} {}".format(f("nick", kwargs), f("message", kwargs))

    # PONG
    # https://tools.ietf.org/html/rfc2812#section-3.7.3
    # PONG [<message>]
    # ----------
    # PONG :I'm still here
    # PONG
    elif command == "PONG":
        if "message" in kwargs:
            return "PONG :" + f("message", kwargs)
        return "PONG"

    # AWAY
    # http://tools.ietf.org/html/rfc2812#section-4.1
    # AWAY [<message>]
    # ----------
    # AWAY :Gone to lunch.
    # AWAY
    elif command == "AWAY":
        if "message" in kwargs:
            return "AWAY :" + f("message", kwargs)
        return "AWAY"

    # REHASH
    # http://tools.ietf.org/html/rfc2812#section-4.2
    # REHASH
    # ----------
    # REHASH
    elif command == "REHASH":
        return "REHASH"

    # DIE
    # http://tools.ietf.org/html/rfc2812#section-4.3
    # DIE
    # ----------
    # DIE
    elif command == "DIE":
        return "DIE"

    # RESTART
    # http://tools.ietf.org/html/rfc2812#section-4.4
    # RESTART
    # ----------
    # RESTART
    elif command == "RESTART":
        return "RESTART"

    # SUMMON
    # http://tools.ietf.org/html/rfc2812#section-4.5
    # SUMMON <nick> [<channel>]
    # ----------
    # SUMMON Wiz #Finnish
    # SUMMON Wiz
    elif command == "SUMMON":
        base = "SUMMON " + f("nick", kwargs)
        if "channel" in kwargs:
            return base + " " + f("channel", kwargs)
        return base

    # USERS
    # http://tools.ietf.org/html/rfc2812#section-4.6
    # USERS
    # ----------
    # USERS
    elif command == "USERS":
        return "USERS"

    # WALLOPS
    # http://tools.ietf.org/html/rfc2812#section-4.7
    # WALLOPS <message>
    # ----------
    # WALLOPS :Maintenance in 5 minutes
    elif command == "WALLOPS":
        return "WALLOPS :" + f("message", kwargs)

    # USERHOST
    # http://tools.ietf.org/html/rfc2812#section-4.8
    # USERHOST <nick>
    # ----------
    # USERHOST Wiz Michael syrk
    # USERHOST syrk
    elif command == "USERHOST":
        return "USERHOST " + pack("nick", kwargs, sep=" ")

    # ISON
    # http://tools.ietf.org/html/rfc2812#section-4.9
    # ISON <nick>
    # ----------
    # ISON Wiz Michael syrk
    # ISON syrk
    elif command == "ISON":
        return "ISON " + pack("nick", kwargs, sep=" ")

    else:
        raise ValueError("Unknown command '{}'".format(command))
