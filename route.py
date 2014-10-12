''' Unpack parsed fields to amtch expected function signatures '''
import inspect
import logging
logger = logging.getLogger(__name__)


class Route(object):
    '''
    Routes should only be used for parsing and dispatching inbound messages.
    Outbound messages should still be serialized by hand.

    '''
    _routes = {}

    command = ''
    ''' The name of the command handled by this route '''

    parameters = []
    ''' The list of fields available, such as nick, channel, message '''

    @classmethod
    def unpack(cls, prefix, params, message):
        ''' Each route must implement this, returning a dict '''
        raise NotImplementedError


def known(command):
    return command.upper() in Route._routes


def get_route(command):
    try:
        return Route._routes[command.upper()]
    except KeyError:
        raise ValueError("Don't know how to route '{}'".format(command))


def validate(command, func):
    route = get_route(command)
    sig = inspect.signature(func)
    expected = set(sig.parameters)
    available = set(route.parameters)
    unavailable = expected - available
    if unavailable:
        raise ValueError(
            ("function '{}' expects the following parameters for command {} "
             + "that are not available: {}.  Available parameters for this "
             + "command are: {}").format(func.__name__, command,
                                         unavailable, available))
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


def unpack(prefix, command, params, message):
    try:
        route = get_route(command)
        return route.command.upper(), route.unpack(prefix, params, message)
    except ValueError:
        logger.info("---UNPACK--- :{} {} {} :{}".format(prefix, command, params, message))
        return command.upper(), {}


def register(route):
    '''
    Register a Route class with the base class

    This could be accomplished in a metaclass but that seems like overkill.

    '''
    command = route.command.upper()
    if known(command):
        raise ValueError("Route for {} already known.".format(command))
    Route._routes[command] = route


# =================================
#
# CUSTOM ROUTES FOR CLIENT-SIDE OPS
#
# =================================

class ClientConnectRoute(Route):
    command = 'CLIENT_CONNECT'
    parameters = ['host', 'port']
register(ClientConnectRoute)


class ClientDisconnectRoute(Route):
    command = 'CLIENT_DISCONNECT'
    parameters = ['host', 'port']
register(ClientDisconnectRoute)

# ===================================
#
# ROUTES FOR RFC SECTIONS 3, 4 FOLLOW
# http://tools.ietf.org/html/rfc2812
#
# ===================================


class PingRoute(Route):
    command = 'PING'
    parameters = ['message']

    @classmethod
    def unpack(cls, prefix, params, message):
        return {'message': message}
register(PingRoute)


class NoticeRoute(Route):
    command = 'NOTICE'
    parameters = ['nick', 'user', 'host', 'target', 'message']
    empty = {
        'nick': None,
        'user': None,
        'host': None,
        'target': None,
        'message': None
    }

    @classmethod
    def unpack(cls, prefix, params, message):
        kwargs = NoticeRoute.empty.copy()
        if '!' in prefix:
            nick, remainder = prefix.split('!', 1)
            kwargs['nick'] = nick
            if '@' in remainder:
                kwargs['user'], kwargs['host'] = remainder.split('@', 1)
            else:
                kwargs['user'] = remainder
        kwargs['target'] = params[0]
        kwargs['message'] = message
        return kwargs
register(NoticeRoute)


class PrivMsgRoute(Route):
    command = 'PRIVMSG'
    parameters = ['nick', 'user', 'host', 'target', 'message']
    empty = {
        'nick': None,
        'user': None,
        'host': None,
        'target': None,
        'message': None
    }

    @classmethod
    def unpack(cls, prefix, params, message):
        kwargs = PrivMsgRoute.empty.copy()
        if '!' in prefix:
            nick, remainder = prefix.split('!', 1)
            kwargs['nick'] = nick
            if '@' in remainder:
                kwargs['user'], kwargs['host'] = remainder.split('@', 1)
            else:
                kwargs['user'] = remainder
        kwargs['target'] = params[0]
        kwargs['message'] = message
        return kwargs
register(PrivMsgRoute)


class JoinRoute(Route):
    command = 'JOIN'
    parameters = ['nick', 'user', 'host', 'channel', 'message']
    empty = {
        'nick': None,
        'user': None,
        'host': None,
        'channel': None,
        'message': None
    }

    @classmethod
    def unpack(cls, prefix, params, message):
        kwargs = PrivMsgRoute.empty.copy()
        if '!' in prefix:
            nick, remainder = prefix.split('!', 1)
            kwargs['nick'] = nick
            if '@' in remainder:
                kwargs['user'], kwargs['host'] = remainder.split('@', 1)
            else:
                kwargs['user'] = remainder
        kwargs['channel'] = params[0]
        kwargs['message'] = message
        return kwargs
register(JoinRoute)


class PartRoute(Route):
    command = 'PART'
    parameters = ['nick', 'user', 'host', 'channel', 'message']
    empty = {
        'nick': None,
        'user': None,
        'host': None,
        'channel': None,
        'message': None
    }

    @classmethod
    def unpack(cls, prefix, params, message):
        kwargs = PrivMsgRoute.empty.copy()
        if '!' in prefix:
            nick, remainder = prefix.split('!', 1)
            kwargs['nick'] = nick
            if '@' in remainder:
                kwargs['user'], kwargs['host'] = remainder.split('@', 1)
            else:
                kwargs['user'] = remainder
        kwargs['channel'] = params[0]
        kwargs['message'] = message
        return kwargs
register(PartRoute)


class QuitRoute(Route):
    command = 'QUIT'
    parameters = ['nick', 'user', 'host', 'message']
    empty = {
        'nick': None,
        'user': None,
        'host': None,
        'message': None
    }

    @classmethod
    def unpack(cls, prefix, params, message):
        kwargs = PrivMsgRoute.empty.copy()
        if '!' in prefix:
            nick, remainder = prefix.split('!', 1)
            kwargs['nick'] = nick
            if '@' in remainder:
                kwargs['user'], kwargs['host'] = remainder.split('@', 1)
            else:
                kwargs['user'] = remainder
        kwargs['message'] = message
        return kwargs
register(QuitRoute)


class RplWelcomeRoute(Route):
    command = 'RPL_WELCOME'
    paramters = ['host', 'message', 'nick']

    @classmethod
    def unpack(cls, prefix, params, message):
        return {
            'host': prefix,
            'message': message,
            'nick': params[0]
        }
register(RplWelcomeRoute)


class RplYourHostRoute(Route):
    command = 'RPL_YOURHOST'
    paramters = ['host', 'message', 'nick']

    @classmethod
    def unpack(cls, prefix, params, message):
        return {
            'host': prefix,
            'message': message,
            'nick': params[0]
        }
register(RplYourHostRoute)


class RplCreatedRoute(Route):
    command = 'RPL_CREATED'
    paramters = ['host', 'message', 'nick']

    @classmethod
    def unpack(cls, prefix, params, message):
        return {
            'host': prefix,
            'message': message,
            'nick': params[0]
        }
register(RplCreatedRoute)


class RplMyInfoRoute(Route):
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
register(RplMyInfoRoute)


class RplBounceRoute(Route):
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
register(RplBounceRoute)


class RplLUserClientRoute(Route):
    command = 'RPL_LUSERCLIENT'
    paramters = ['host', 'message', 'nick']

    @classmethod
    def unpack(cls, prefix, params, message):
        return {
            'host': prefix,
            'message': message,
            'nick': params[0]
        }
register(RplLUserClientRoute)


class RplLUserOpRoute(Route):
    command = 'RPL_LUSEROP'
    paramters = ['host', 'message', 'nick', 'count']

    @classmethod
    def unpack(cls, prefix, params, message):
        return {
            'host': prefix,
            'message': message,
            'nick': params[0],
            'count': int(params[1])
        }
register(RplLUserOpRoute)


class RplLUserUnknownRoute(Route):
    command = 'RPL_LUSERUNKNOWN'
    paramters = ['host', 'message', 'nick', 'count']

    @classmethod
    def unpack(cls, prefix, params, message):
        return {
            'host': prefix,
            'message': message,
            'nick': params[0],
            'count': int(params[1])
        }
register(RplLUserUnknownRoute)


class RplLUserChannelsRoute(Route):
    command = 'RPL_LUSERCHANNELS'
    paramters = ['host', 'message', 'nick', 'count']

    @classmethod
    def unpack(cls, prefix, params, message):
        return {
            'host': prefix,
            'message': message,
            'nick': params[0],
            'count': int(params[1])
        }
register(RplLUserChannelsRoute)


class RplLUserMeRoute(Route):
    command = 'RPL_LUSERME'
    paramters = ['host', 'message', 'nick']

    @classmethod
    def unpack(cls, prefix, params, message):
        return {
            'host': prefix,
            'message': message,
            'nick': params[0]
        }
register(RplLUserMeRoute)


class RplStatsDLineRoute(Route):
    command = 'RPL_STATSDLINE'
    paramters = ['host', 'message', 'nick']

    @classmethod
    def unpack(cls, prefix, params, message):
        return {
            'host': prefix,
            'message': message,
            'nick': params[0]
        }
register(RplStatsDLineRoute)


class RplMOTDStartRoute(Route):
    command = 'RPL_MOTDSTART'
    paramters = ['host', 'message', 'nick']

    @classmethod
    def unpack(cls, prefix, params, message):
        return {
            'host': prefix,
            'message': message,
            'nick': params[0]
        }
register(RplMOTDStartRoute)


class RplMOTDRoute(Route):
    command = 'RPL_MOTD'
    paramters = ['host', 'message', 'nick']

    @classmethod
    def unpack(cls, prefix, params, message):
        return {
            'host': prefix,
            'message': message,
            'nick': params[0]
        }
register(RplMOTDRoute)


class RplEndOfMOTDRoute(Route):
    command = 'RPL_ENDOFMOTD'
    paramters = ['host', 'message', 'nick']

    @classmethod
    def unpack(cls, prefix, params, message):
        return {
            'host': prefix,
            'message': message,
            'nick': params[0]
        }
register(RplEndOfMOTDRoute)
