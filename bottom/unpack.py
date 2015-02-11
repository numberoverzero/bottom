""" Simplified support for rfc2812 """
# https://tools.ietf.org/html/rfc2812
import re
missing = object()

RE_IRCLINE = re.compile(
    """
    ^
    (:(?P<prefix>[^\s]+)\s+)?    # Optional prefix (src, nick!host, etc)
                                 # Prefix matches all non-space characters
                                 # Must start with a ':' character

    (?P<command>[^:\s]+)          # Command is required (JOIN, 001, 403)
                                 # Command matches all non-space characters

    (?P<params>(\s+[^:][^\s]*)*) # Optional params after command
                                 # Must have at least one leading space
                                 # Params end at first ':' which starts message

    (?:\s+:(?P<message>.*))?     # Optional message starts after first ':'
                                 # Must have at least one leading space
    $
    """, re.VERBOSE)

_2812_synonyms = {}
for numeric, string in [
    ("001", "RPL_WELCOME"),
    ("002", "RPL_YOURHOST"),
    ("003", "RPL_CREATED"),
    ("004", "RPL_MYINFO"),
    ("005", "RPL_BOUNCE"),
    ("302", "RPL_USERHOST"),
    ("303", "RPL_ISON"),
    ("301", "RPL_AWAY"),
    ("305", "RPL_UNAWAY"),
    ("306", "RPL_NOWAWAY"),
    ("311", "RPL_WHOISUSER"),
    ("312", "RPL_WHOISSERVER"),
    ("313", "RPL_WHOISOPERATOR"),
    ("317", "RPL_WHOISIDLE"),
    ("318", "RPL_ENDOFWHOIS"),
    ("319", "RPL_WHOISCHANNELS"),
    ("314", "RPL_WHOWASUSER"),
    ("369", "RPL_ENDOFWHOWAS"),
    ("321", "RPL_LISTSTART"),
    ("322", "RPL_LIST"),
    ("323", "RPL_LISTEND"),
    ("325", "RPL_UNIQOPIS"),
    ("324", "RPL_CHANNELMODEIS"),
    ("331", "RPL_NOTOPIC"),
    ("332", "RPL_TOPIC"),
    ("341", "RPL_INVITING"),
    ("342", "RPL_SUMMONING"),
    ("346", "RPL_INVITELIST"),
    ("347", "RPL_ENDOFINVITELIST"),
    ("348", "RPL_EXCEPTLIST"),
    ("349", "RPL_ENDOFEXCEPTLIST"),
    ("351", "RPL_VERSION"),
    ("352", "RPL_WHOREPLY"),
    ("315", "RPL_ENDOFWHO"),
    ("353", "RPL_NAMREPLY"),
    ("366", "RPL_ENDOFNAMES"),
    ("364", "RPL_LINKS"),
    ("365", "RPL_ENDOFLINKS"),
    ("367", "RPL_BANLIST"),
    ("368", "RPL_ENDOFBANLIST"),
    ("371", "RPL_INFO"),
    ("374", "RPL_ENDOFINFO"),
    ("375", "RPL_MOTDSTART"),
    ("372", "RPL_MOTD"),
    ("376", "RPL_ENDOFMOTD"),
    ("381", "RPL_YOUREOPER"),
    ("382", "RPL_REHASHING"),
    ("383", "RPL_YOURESERVICE"),
    ("391", "RPL_TIME"),
    ("392", "RPL_USERSSTART"),
    ("393", "RPL_USERS"),
    ("394", "RPL_ENDOFUSERS"),
    ("395", "RPL_NOUSERS"),
    ("200", "RPL_TRACELINK"),
    ("201", "RPL_TRACECONNECTING"),
    ("202", "RPL_TRACEHANDSHAKE"),
    ("203", "RPL_TRACEUNKNOWN"),
    ("204", "RPL_TRACEOPERATOR"),
    ("205", "RPL_TRACEUSER"),
    ("206", "RPL_TRACESERVER"),
    ("207", "RPL_TRACESERVICE"),
    ("208", "RPL_TRACENEWTYPE"),
    ("209", "RPL_TRACECLASS"),
    ("210", "RPL_TRACERECONNECT"),
    ("261", "RPL_TRACELOG"),
    ("262", "RPL_TRACEEND"),
    ("211", "RPL_STATSLINKINFO"),
    ("212", "RPL_STATSCOMMANDS"),
    ("219", "RPL_ENDOFSTATS"),
    ("242", "RPL_STATSUPTIME"),
    ("243", "RPL_STATSOLINE"),
    ("221", "RPL_UMODEIS"),
    ("234", "RPL_SERVLIST"),
    ("235", "RPL_SERVLISTEND"),
    ("251", "RPL_LUSERCLIENT"),
    ("252", "RPL_LUSEROP"),
    ("253", "RPL_LUSERUNKNOWN"),
    ("254", "RPL_LUSERCHANNELS"),
    ("255", "RPL_LUSERME"),
    ("256", "RPL_ADMINME"),
    ("257", "RPL_ADMINLOC1"),
    ("258", "RPL_ADMINLOC2"),
    ("259", "RPL_ADMINEMAIL"),
    ("263", "RPL_TRYAGAIN"),
    ("401", "ERR_NOSUCHNICK"),
    ("402", "ERR_NOSUCHSERVER"),
    ("403", "ERR_NOSUCHCHANNEL"),
    ("404", "ERR_CANNOTSENDTOCHAN"),
    ("405", "ERR_TOOMANYCHANNELS"),
    ("406", "ERR_WASNOSUCHNICK"),
    ("407", "ERR_TOOMANYTARGETS"),
    ("408", "ERR_NOSUCHSERVICE"),
    ("409", "ERR_NOORIGIN"),
    ("411", "ERR_NORECIPIENT"),
    ("412", "ERR_NOTEXTTOSEND"),
    ("413", "ERR_NOTOPLEVEL"),
    ("414", "ERR_WILDTOPLEVEL"),
    ("415", "ERR_BADMASK"),
    ("421", "ERR_UNKNOWNCOMMAND"),
    ("422", "ERR_NOMOTD"),
    ("423", "ERR_NOADMININFO"),
    ("424", "ERR_FILEERROR"),
    ("431", "ERR_NONICKNAMEGIVEN"),
    ("432", "ERR_ERRONEUSNICKNAME"),
    ("433", "ERR_NICKNAMEINUSE"),
    ("436", "ERR_NICKCOLLISION"),
    ("437", "ERR_UNAVAILRESOURCE"),
    ("441", "ERR_USERNOTINCHANNEL"),
    ("442", "ERR_NOTONCHANNEL"),
    ("443", "ERR_USERONCHANNEL"),
    ("444", "ERR_NOLOGIN"),
    ("445", "ERR_SUMMONDISABLED"),
    ("446", "ERR_USERSDISABLED"),
    ("451", "ERR_NOTREGISTERED"),
    ("461", "ERR_NEEDMOREPARAMS"),
    ("462", "ERR_ALREADYREGISTRED"),
    ("463", "ERR_NOPERMFORHOST"),
    ("464", "ERR_PASSWDMISMATCH"),
    ("465", "ERR_YOUREBANNEDCREEP"),
    ("466", "ERR_YOUWILLBEBANNED"),
    ("467", "ERR_KEYSET"),
    ("471", "ERR_CHANNELISFULL"),
    ("472", "ERR_UNKNOWNMODE"),
    ("473", "ERR_INVITEONLYCHAN"),
    ("474", "ERR_BANNEDFROMCHAN"),
    ("475", "ERR_BADCHANNELKEY"),
    ("476", "ERR_BADCHANMASK"),
    ("477", "ERR_NOCHANMODES"),
    ("478", "ERR_BANLISTFULL"),
    ("481", "ERR_NOPRIVILEGES"),
    ("482", "ERR_CHANOPRIVSNEEDED"),
    ("483", "ERR_CANTKILLSERVER"),
    ("484", "ERR_RESTRICTED"),
    ("485", "ERR_UNIQOPPRIVSNEEDED"),
    ("491", "ERR_NOOPERHOST"),
    ("501", "ERR_UMODEUNKNOWNFLAG"),
    ("502", "ERR_USERSDONTMATCH")
]:
    _2812_synonyms[string] = string
    _2812_synonyms[numeric] = string


def synonym(command):
    command = command.upper()
    return _2812_synonyms.get(command, command)


def nickmask(prefix, kwargs):
    ''' store nick, user, host in kwargs if prefix is correct format '''
    if "!" in prefix and "@" in prefix:
        # From a user
        kwargs['nick'], remainder = prefix.split('!', 1)
        kwargs['user'], kwargs['host'] = remainder.split('@', 1)
    else:
        # From a server, probably the host
        kwargs['host'] = prefix


def add_nickmask(params):
    params.extend(["nick", "user", "host"])


def split_line(msg):
    ''' Parse message according to rfc 2812 for routing '''
    match = RE_IRCLINE.match(msg)
    if not match:
        raise ValueError("Invalid line")

    prefix = match.group("prefix") or ''
    command = match.group("command")
    params = (match.group('params') or '').split()
    message = match.group('message') or ''

    if message:
        params.append(message)

    return prefix, command, params


def unpack_command(msg):
    prefix, command, params = split_line(msg.strip())
    command = synonym(command)
    kwargs = {}

    if command in ["PING", "ERR_NOMOTD"]:
        kwargs["message"] = params[-1]

    elif command in ["PRIVMSG", "NOTICE"]:
        nickmask(prefix, kwargs)
        kwargs["target"] = params[0]
        kwargs["message"] = params[-1]

    elif command in ["JOIN"]:
        nickmask(prefix, kwargs)
        kwargs["channel"] = params[0]

    elif command in ["QUIT"]:
        nickmask(prefix, kwargs)
        if params:
            kwargs["message"] = params[0]
        else:
            kwargs["message"] = ''

    elif command in ["PART"]:
        nickmask(prefix, kwargs)
        kwargs["channel"] = params[0]
        if(len(params) > 1):
            kwargs["message"] = params[-1]
        else:
            kwargs["message"] = ''

    elif command in ["RPL_TOPIC", "RPL_NOTOPIC", "RPL_ENDOFNAMES"]:
        kwargs["channel"] = params[1]
        kwargs["message"] = params[2]

    elif command in ["RPL_MOTDSTART", "RPL_MOTD", "RPL_ENDOFMOTD",
                     "RPL_WELCOME", "RPL_YOURHOST", "RPL_CREATED",
                     "RPL_LUSERCLIENT", "RPL_LUSERME"]:
        kwargs["message"] = params[-1]

    elif command in ["RPL_LUSEROP", "RPL_LUSERUNKNOWN", "RPL_LUSERCHANNELS"]:
        kwargs["count"] = int(params[1])
        if(len(params) > 2):
            kwargs["message"] = params[-1]
        else:
            kwargs["message"] = ''

    elif command in ["RPL_MYINFO", "RPL_BOUNCE"]:
        kwargs["info"] = params[1:-1]
        kwargs["message"] = params[-1]

    else:
        raise ValueError("Unknown command '{}'".format(command))

    return command, kwargs


def parameters(command):
    command = synonym(command)
    params = []

    if command in ["CLIENT_CONNECT", "CLIENT_DISCONNECT"]:
        params.append("host")
        params.append("port")

    elif command in ["PING", "ERR_NOMOTD"]:
        params.append("message")

    elif command in ["PRIVMSG", "NOTICE"]:
        add_nickmask(params)
        params.append("target")
        params.append("message")

    elif command in ["JOIN"]:
        add_nickmask(params)
        params.append("channel")

    elif command in ["QUIT"]:
        add_nickmask(params)
        params.append("message")

    elif command in ["RPL_TOPIC", "RPL_NOTOPIC", "RPL_ENDOFNAMES"]:
        params.append("channel")
        params.append("message")

    elif command in ["PART"]:
        add_nickmask(params)
        params.append("channel")
        params.append("message")

    elif command in ["RPL_MOTDSTART", "RPL_MOTD", "RPL_ENDOFMOTD",
                     "RPL_WELCOME", "RPL_YOURHOST", "RPL_CREATED",
                     "RPL_LUSERCLIENT", "RPL_LUSERME"]:
        params.append("message")

    elif command in ["RPL_LUSEROP", "RPL_LUSERUNKNOWN", "RPL_LUSERCHANNELS"]:
        params.append("count")
        params.append("message")

    elif command in ["RPL_MYINFO", "RPL_BOUNCE"]:
        params.append("info")
        params.append("message")

    else:
        raise ValueError("Unknown command '{}'".format(command))

    return params
