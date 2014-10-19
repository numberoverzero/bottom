""" Simplified support for rfc2812 """
# http://tools.ietf.org/html/rfc2812
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


def nickmask(prefix, kwargs):
    ''' store nick, user, host in kwargs if prefix is correct format '''
    kwargs['nick'], remainder = prefix.split('!', 1)
    kwargs['user'], kwargs['host'] = remainder.split('@', 1)


def add_nickmask(params):
    params.extend(["nick", "user", "host"])


def split_line(msg):
    ''' Parse message according to rfc 2812 for routing '''
    match = RE_IRCLINE.match(msg)
    if not match:
        raise ValueError("Invalid line")

    prefix = match.group("prefix") or ''
    command = match.group("command").upper()
    params = (match.group('params') or '').split()
    message = match.group('message') or ''

    return prefix, command, params, message


def unpack_command(msg):
    prefix, command, params, message = split_line(msg)
    kwargs = {}

    if command == "PING":
        kwargs["message"] = message

    elif command in ["PRIVMSG", "NOTICE"]:
        nickmask(prefix, kwargs)
        kwargs["target"] = params[0]
        kwargs["message"] = message

    elif command == "JOIN":
        nickmask(prefix, kwargs)
        kwargs["channel"] = params[0]

    elif command == "PART":
        nickmask(prefix, kwargs)
        kwargs["channel"] = params[0]
        kwargs["message"] = message

    else:
        raise ValueError("Unknown command '{}'".format(command))

    return command, kwargs


def parameters(command):
    command = command.upper()
    params = []

    if command in ["CLIENT_CONNECT", "CLIENT_DISCONNECT"]:
        params.append("host")
        params.append("port")

    elif command == "PING":
        params.append("message")

    elif command in ["PRIVMSG", "NOTICE"]:
        add_nickmask(params)
        params.append("target")
        params.append("message")

    elif command == "JOIN":
        add_nickmask(params)
        params.append("channel")

    elif command == "PART":
        add_nickmask(params)
        params.append("channel")
        params.append("message")

    else:
        raise ValueError("Unknown command '{}'".format(command))

    return params
