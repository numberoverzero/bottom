''' Unpack parsed fields to amtch expected function signatures '''
import inspect
import logging
logger = logging.getLogger(__name__)

__all__ = ["unpack", "validate"]


def user_prefix(prefix, kwargs):
    if '!' in prefix:
        nick, remainder = prefix.split('!', 1)
        kwargs['nick'] = nick
        if '@' in remainder:
            kwargs['user'], kwargs['host'] = remainder.split('@', 1)
        else:
            kwargs['user'] = remainder
    else:
        kwargs['user'] = prefix


def msg_parser(prefix, params, message):
    kwargs = {}
    user_prefix(prefix, kwargs)
    kwargs['target'] = params[0]
    kwargs['message'] = message
    return kwargs


def channel_parser(prefix, params, message):
    kwargs = {}
    user_prefix(prefix, kwargs)
    kwargs['channel'] = params[0]
    kwargs['message'] = message
    return kwargs


def quit_parser(prefix, params, message):
    kwargs = {}
    user_prefix(prefix, kwargs)
    kwargs['message'] = message
    return kwargs


parser_config = [
    {
        "commands": ["PING"],
        "parameters": ["message"],
        "parser": lambda _, __, message: {"message": message}
    },
    {
        "commands": ["CLIENT_CONNECT", "CLIENT_DISCONNECT"],
        "parameters": ["host", "port"]
        # No parser - client-side event
    },
    {
        "commands": ["NOTICE", "PRIVMSG"],
        "parameters": ["nick", "user", "host", "target", "message"],
        "parser": msg_parser
    },
    {
        "commands": ["JOIN", "PART"],
        "parameters": ["nick", "user", "host", "channel", "message"],
        "parser": channel_parser
    },
    {
        "commands": ["QUIT"],
        "parameters": ["nick", "user", "host", "message"],
        "parser": quit_parser
    },
    {
        "commands": ["RPL_MOTDSTART", "RPL_MOTD", "RPL_ENDOFMOTD",
                     "RPL_WELCOME", "RPL_YOURHOST", "RPL_CREATED",
                     "RPL_LUSERCLIENT", "RPL_LUSERME", "RPL_STATSDLINE"],
        "parameters": ["host", "message"],
        "parser": lambda host, _, msg: {"host": host, "message": msg}
    },
    {
        "commands": ["RPL_LUSEROP", "RPL_LUSERUNKNOWN", "RPL_LUSERCHANNELS"],
        "parameters": ["host", "message", "count"],
        "parser": lambda h, p, m: {"host": h, "message": m, "count": int(p[1])}
    }
]

PARSERS = {}

for config_block in parser_config:
    for command in config_block["commands"]:
        parameters = config_block["parameters"]
        parser = config_block.get("parser", None)
        PARSERS[command.upper()] = [parameters, parser]


def validate(command, func):
    command = command.upper()
    try:
        parameters, parser = PARSERS[command]
    except KeyError:
        raise ValueError("Unknown command '{}'".format(command))
    sig = inspect.signature(func)
    for param in sig.parameters.values():
        kind = param.kind
        if kind == inspect.Parameter.VAR_POSITIONAL:
            raise ValueError(
                ("function '{}' expects parameter {} to be VAR_POSITIONAL, "
                 + "when it will always be a single value.  This parameter "
                 + "must be either POSITIONAL_ONLY, POSITIONAL_OR_KEYWORD, or "
                 + "KEYWORD_ONLY.").format(func.__name__, param.name))
        if kind == inspect.Parameter.VAR_KEYWORD:
            raise ValueError(
                ("function '{}' expects parameter {} to be VAR_KEYWORD, "
                 + "when it will always be a single value.  This parameter "
                 + "must be either POSITIONAL_ONLY, POSITIONAL_OR_KEYWORD, or "
                 + "KEYWORD_ONLY.").format(func.__name__, param.name))
    expected = set(sig.parameters)
    available = set(parameters)
    unavailable = expected - available
    if unavailable:
        raise ValueError(
            ("function '{}' expects the following parameters for command {} "
             + "that are not available: {}.  Available parameters for this "
             + "command are: {}").format(func.__name__, command,
                                         unavailable, available))


def unpack(prefix, command, params, message):
    command = command.upper()
    try:
        _, parser = PARSERS[command]
        return command, parser(prefix, params, message)
    except KeyError:
        logger.info(("Tried to unpack unknown command '{}' with prefix, "
                    + "params, message :{} {} :{}")
                    .format(command, prefix, params, message))
        return command, {}

# ===================================
#
# ROUTES FOR RFC SECTIONS 3, 4 FOLLOW
# http://tools.ietf.org/html/rfc2812
#
# ===================================


class RplMyInfoRoute(object):
    command = 'RPL_MYINFO'
    paramters = ['host', 'message', 'nick', 'info']

    @classmethod
    def unpack(cls, prefix, params, message):
        return {
            'host': prefix,
            'message': message,
            'nick': params[0],
            'info': params[1:]
        }


class RplBounceRoute(object):
    command = 'RPL_BOUNCE'
    paramters = ['host', 'message', 'nick', 'config']

    @classmethod
    def unpack(cls, prefix, params, message):
        return {
            'host': prefix,
            'message': message,
            'nick': params[0],
            'config': params[1:]
        }
