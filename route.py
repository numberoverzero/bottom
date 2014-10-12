''' Unpack parsed fields to amtch expected function signatures '''
import inspect
missing = object()  # sentinel


class PartialDefer(object):
    ''' Custom partial binding for functions that map to commands '''
    def __init__(self, command, func):
        self.sig = inspect.signature(func)
        self.command = command
        self.func = func

        self.load_defaults()

    def load_defaults(self):
        '''
        Only set defaults for keys the function expects

        Functions may not expect all available parameters for the command, so
        we only build a mapping for the ones we care about.

        '''
        self.default = {}
        for key, param in self.sig.parameters.items():
            default = param.default
            #  Has no default - use equivalent of empty
            if default is inspect.Parameter.empty:
                self.default[key] = None
            else:
                self.default[key] = default

    def __call__(self, kwargs):
        unbound = self.default.copy()
        # Only map params this function expects
        for key in unbound:
            new_value = kwargs.get(key, missing)
            # Don't overwrite defaults with nothing
            if new_value not in [missing, None]:
                unbound[key] = new_value
        bound = self.sig.bind(**unbound)
        self.func(*bound.args, **bound.kwargs)

partial_bind = PartialDefer  # alias


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
    route = Route.get_route(command)
    sig = inspect.signature(func)
    expected = set(sig.parameters)
    available = set(route.parameters)
    unavailable = expected - available
    if unavailable:
        raise ValueError(
            "function '{}' expects the following parameters for command {} "
            + "that are not available: {}.  Available parameters for this "
            + "command are: {}".format(func.__name__, command,
                                       unavailable, available))
    for param in sig.parameters.values():
        kind = param.kind
        if kind == inspect.Parameter.VAR_POSITIONAL:
            raise ValueError(
                "function '{}' expects parameter {} to be VAR_POSITIONAL, "
                + "when it will always be a single value.  This parameter "
                + "must be either POSITIONAL_ONLY, POSITIONAL_OR_KEYWORD, or "
                + "KEYWORD_ONLY.".format(func.__name__, param.name))
        if kind == inspect.Parameter.VAR_KEYWORD:
            raise ValueError(
                "function '{}' expects parameter {} to be VAR_KEYWORD, "
                + "when it will always be a single value.  This parameter "
                + "must be either POSITIONAL_ONLY, POSITIONAL_OR_KEYWORD, or "
                + "KEYWORD_ONLY.".format(func.__name__, param.name))


def unpack(prefix, command, params, message):
    route = Route.get_route(command)
    return route.command.upper(), route.unpack(prefix, params, message)


def register(route):
    '''
    Register a Route class with the base class

    This could be accomplished in a metaclass but that seems like overkill.

    '''
    if Route.known(route):
        raise ValueError("Route for {} already known.".format(route.command))
    Route._routes[route.command.upper()] = route


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
