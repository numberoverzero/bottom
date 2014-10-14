''' Parse messages into python args, kwargs according to rfc 2812 '''
#  http://tools.ietf.org/html/rfc2812
import re

__all__ = ["unique_command", "wire_format", "parse"]

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

RAW_COMMANDS = set([
    #  3.1 Connection Registration
    "PASS", "NICK", "USER", "OPER", "MODE", "SERVICE", "QUIT", "SQUIT",
    #  3.2 Channel Operations
    "JOIN", "PART", "MODE", "TOPIC", "NAMES", "LIST", "INVITE", "KICK",
    #  3.3 Sending Messages
    "PRIVMSG", "NOTICE",
    #  3.4 Server Queries and Commands
    "MOTD", "LUSERS", "VERSION", "STATS", "LINKS", "TIME",
    "CONNECT", "TRACE", "ADMIN", "INFO",
    #  3.5 Service Query and Commands
    "SERVLIST", "SQUERY",
    #  3.6 User Based Queries
    "WHO", "WHOIS", "WHOWAS",
    #  3.7 Miscellaneous Messages
    "KILL", "PING", "PONG", "ERROR",
    #  4.0 Optional Features
    "AWAY", "REHASH", "DIE", "RESTART", "SUMMON", "USERS",
    "WALLOPS", "USERHOST", "ISON",
    #  5.0 Replies
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
    ("502", "ERR_USERSDONTMATCH"),

    #  5.3 Reserved Numerics
    ("231", "RPL_SERVICEINFO"),
    ("232", "RPL_ENDOFSERVICES"),
    ("233", "RPL_SERVICE"),
    ("300", "RPL_NONE"),
    ("316", "RPL_WHOISCHANOP"),
    ("361", "RPL_KILLDONE"),
    ("362", "RPL_CLOSING"),
    ("363", "RPL_CLOSEEND"),
    ("373", "RPL_INFOSTART"),
    ("384", "RPL_MYPORTIS"),
    ("213", "RPL_STATSCLINE"),
    ("214", "RPL_STATSNLINE"),
    ("215", "RPL_STATSILINE"),
    ("216", "RPL_STATSKLINE"),
    ("217", "RPL_STATSQLINE"),
    ("218", "RPL_STATSYLINE"),
    ("240", "RPL_STATSVLINE"),
    ("241", "RPL_STATSLLINE"),
    ("244", "RPL_STATSHLINE"),
    ("244", "RPL_STATSSLINE"),
    ("246", "RPL_STATSPING"),
    ("247", "RPL_STATSBLINE"),
    ("250", "RPL_STATSDLINE"),
    ("492", "ERR_NOSERVICEHOST"),
])

# Dict maps from raw string to de-duped command type
# This makes it unambiguous to talk about the command "RPL_WELCOME" even though
# it can be represented by either "RPL_WELCOME" or "001"
COMMANDS = {}
WIRE_COMMANDS = {}
for entry in RAW_COMMANDS:
    # Single representation
    if isinstance(entry, str):
        COMMANDS[entry] = entry
        WIRE_COMMANDS[entry] = entry
    # Numeric <--> str pair
    elif isinstance(entry, tuple):
        assert len(entry) == 2
        number, string = entry
        COMMANDS[number] = string
        COMMANDS[string] = string
        WIRE_COMMANDS[number] = number
        WIRE_COMMANDS[string] = number
    # Typo in setup
    else:
        raise ValueError(
            "Unexpected entry in RAW_COMMANDS: '{}'".format(entry))


def unique_command(command):
    '''
    Return the unique string that a command maps to

    If input command isn't known, returns the uppercase version.
    '''
    command = command.upper()
    try:
        return COMMANDS[command]
    except KeyError:
        return command


def wire_command(command):
    '''
    Return the representation a command uses on the wire

    If input command isn't known, returns the uppercase version.
    '''
    command = command.upper()
    try:
        return WIRE_COMMANDS[command]
    except KeyError:
        return command


def wire_format(command, params=None, message=None, prefix=None):
    """ Return the correct wire format of a command """
    s = ''
    if prefix:
        s += ":{} ".format(prefix)
    s += wire_command(command)
    if params:
        for param in params:
            s += " " + str(param)
    if message:
        s += " :{}".format(message)
    return s


def normalize(match):
    prefix = match.group("prefix")
    command = match.group("command")
    params = match.group('params')
    message = match.group('message')

    # Normalize
    prefix = prefix or ''
    command = unique_command(command)
    params = (params or '').split()
    message = message or ''

    return prefix, command, params, message


def parse(msg):
    ''' Parse message according to rfc 2812 for routing '''
    match = RE_IRCLINE.match(msg)
    if not match:
        return None
    #  prefix, command, params, message
    return normalize(match)
