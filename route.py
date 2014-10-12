''' Unpack parsed fields to amtch expected function signatures '''
import inspect
missing = object()  # sentinel

ROUTES = {
    "CLIENT_CONNECT": None,
    "CLIENT_DISCONNECT": None,
    "PING": None
}


def known(command):
    command = command.upper()
    return command in ROUTES


def validate(command, func):
    command = command.upper()
    if not known(command):
        raise ValueError("Don't know how to route '{}'".format(command))
    sig = inspect.signature(func)
    expected = set(sig.parameters)
    available = set(ROUTES[command].parameters)
    unavailable = expected - available
    if unavailable:
        raise ValueError("function '{}' expects the following parameters for "
                         + "command {} that are not available: {}.  Available "
                         + "parameters for this command are: {}".format(
                             func.__name__, command, unavailable, available))
    for param in sig.parameters.values():
        kind = param.kind
        if kind == inspect.Parameter.VAR_POSITIONAL:
            raise ValueError("function '{}' expects parameter {} to be "
                             + "VAR_POSITIONAL, when it will always be a "
                             + "single value.  This parameter must be either "
                             + "POSITIONAL_ONLY, POSITIONAL_OR_KEYWORD, or "
                             + "KEYWORD_ONLY.".format(
                                 func.__name__, param.name))
        if kind == inspect.Parameter.VAR_KEYWORD:
            raise ValueError("function '{}' expects parameter {} to be "
                             + "VAR_KEYWORD, when it will always be a single "
                             + "value.  This parameter must be either "
                             + "POSITIONAL_ONLY, POSITIONAL_OR_KEYWORD, or "
                             + "KEYWORD_ONLY.".format(
                                 func.__name__, param.name))


def unpack(prefix, command, params, message):
    ''' Map from IRC components to reasonable python structures '''
    command = command.upper()
    if not known(command):
        raise ValueError("Don't know how to unpack '{}'".format(command))
    kwargs = {}
    raise NotImplementedError
    return command, kwargs


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
