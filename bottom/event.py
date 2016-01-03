import asyncio
import collections
import inspect
from typing import Callable, Dict

missing = object()


class EventsMixin(object):
    def __init__(self, getparams: Callable, *,
                 loop: asyncio.BaseEventLoop) -> None:
        """
        getparams is a function that takes a single argument (event) and
        returns a list of parameters for the event.  It should raise on unknown
        events.
        """

        # Dictionary of event : list(func)
        # where event is a string, and list(func) is the list of functions
        # (wrapped and decorated) that will be invoked when the given event
        # is triggered.
        self._partials = collections.defaultdict(list)
        self._getparams = getparams
        self.loop = loop

    def _add_event(self, event: str, func: Callable) -> Callable:
        """
        Validate the func's signature, then partial_bind the function to speed
        up argument injection.

        """
        parameters = self._getparams(event)
        validate_func(event, func, parameters)
        self._partials[event].append(partial_bind(func))
        return func

    def trigger(self, event: str, **kwargs) -> None:
        """
        Triggers an event across a registered listeners.
        :param event: The event to trigger.
        :param kwargs: Any keyword arguments to pass to called listeners.
        """
        partials = self._partials[event]
        for func in partials:
            self.loop.create_task(func(**kwargs))

    def on(self, event: str) -> Callable:
        """
        Decorate a function to be invoked when the given :param:`event` occurs.
        The function may be a coroutine.

        Returns
        -------
        A decorator that takes a function and registers it with the event.

        Example:

        .. code-block:: python

            import asyncio

            events = EventsMixin({'test': ['arg', 'one', 'two']})

            @events.on('test')
            def func(one, arg):
                print(arg, one)

            event = 'test'
            kwargs = {'one': 1, 'two': 2, 'arg': 'arg'}

            events.trigger(event, **kwargs)
            loop = asyncio.get_event_loop()
            # Run all queued events
            loop.stop()
            loop.run_forever()

        :param event: The name of the event to wait for.
        :returns: The wrapped function.
        """

        def wrap_function(func):
            self._add_event(event, func)
            return func

        return wrap_function


def validate_func(event: str, func: Callable, parameters: Dict):
    """
    Validates the signature of a function against the expected arguments
    for a given event type.

    :param event: The type of event to validate against.
    :param func: The function to validate.
    :param parameters: The expected parameters of the function.
    """
    sig = inspect.signature(func)
    expected = set(sig.parameters)
    for param in sig.parameters.values():
        kind = param.kind
        if kind == inspect.Parameter.VAR_POSITIONAL:
            raise ValueError(
                    (
                        "function '{}' expects parameter {} to be VAR_POSITIONAL, "
                        + "when it will always be a single value.  This parameter "
                        + "must be either POSITIONAL_ONLY, POSITIONAL_OR_KEYWORD, or "
                        + "KEYWORD_ONLY (or omitted)").format(func.__name__,
                                                              param.name))
        if kind == inspect.Parameter.VAR_KEYWORD:
            # **kwargs are ok, as long as the **name doesn't
            # mask an actual param that the event emits.
            if param.name in parameters:
                # masking :(
                raise ValueError(
                        (
                            "function '{}' expects parameter {} to be VAR_KEYWORD, "
                            + "which masks an actual parameter for event {}.  This "
                              "event has the following parameters, which must not be "
                              "used as the **VAR_KEYWORD argument.  They may be "
                              "omitted").format(
                                func.__name__, param.name, event, parameters))
            else:
                # Pop from expected, this will gobble up any unused params
                expected.remove(param.name)

    available = set(parameters)
    unavailable = expected - available
    if unavailable:
        raise ValueError(
                ("function '{}' expects the following parameters for event {} "
                 + "that are not available: {}.  Available parameters for this "
                 + "event are: {}").format(func.__name__, event,
                                           unavailable, available))


def partial_bind(func: Callable) -> Callable:
    sig = inspect.signature(func)
    # Wrap non-coroutines so we can always `await func(**kw)`
    if not asyncio.iscoroutinefunction(func):
        func = asyncio.coroutine(func)
    base = {}
    for key, param in sig.parameters.items():
        default = param.default
        #  Param has no default - use equivalent of empty
        if default is inspect.Parameter.empty:
            base[key] = None
        else:
            base[key] = default

    async def wrapper(**kwargs) -> None:
        unbound = base.copy()
        # Only map params this function expects
        for key in base:
            new_value = kwargs.get(key, missing)
            if new_value is not missing:
                unbound[key] = new_value
        bound = sig.bind(**unbound)
        await func(*bound.args, **bound.kwargs)

    return wrapper
