from bottom import event
import asyncio
import pytest


@pytest.fixture
def getparams():
    params = {
        "0": [],
        "1": ["one"],
        "2": ["one", "two"]
    }
    return lambda event: params[event]


@pytest.fixture
def events(getparams):
    return event.EventsMixin(getparams)


@pytest.fixture
def run():
    loop = asyncio.get_event_loop()
    return lambda coro: loop.run_until_complete(coro)


@pytest.fixture
def watch():
    class Watcher():
        def __init__(self):
            self.calls = 0

        def call(self):
            self.calls += 1

        @property
        def called(self):
            return self.calls > 0
    return Watcher


# ==============
# EventsMixin.on
# ==============


def test_on_subset(events):
    ''' register a handler with a subset of available parameters '''
    subset = lambda: None
    for e in ["0", "1", "2"]:
        events.on(e)(subset)


def test_on_all(events):
    ''' register a handler with all available parameters '''
    handle = lambda one, two: None
    events.on("2")(handle)


def test_on_superset(events):
    ''' raise when handler expects unavailable parameters '''
    handle = lambda one, two: None
    with pytest.raises(ValueError):
        events.on("1")(handle)


def test_on_ordering(events):
    ''' ordering is irrelevant '''
    handle = lambda two, one: None
    events.on("2")(handle)


def test_with_kwargs(events):
    ''' kwargs is ok without masking '''
    handle = lambda one, **kwargs: None
    events.on("2")(handle)


def test_with_kwargs_masking(events):
    ''' masking kwargs raise '''
    handle = lambda one, **two: None
    with pytest.raises(ValueError):
        events.on("2")(handle)


def test_var_args(events):
    ''' *args are never ok '''
    handle = lambda one, *args: None
    with pytest.raises(ValueError):
        events.on("2")(handle)


def test_defaults(events):
    ''' defaults are fine '''
    handle = lambda one="foo", two="bar": None
    events.on("2")(handle)


def test_on_coroutine(events):
    ''' coroutines are fine '''
    handle = asyncio.coroutine(lambda one: None)
    events.on("1")(handle)


# ===================
# EventsMixin.trigger
# ===================

def test_trigger(events, run, watch):
    ''' trigger calls registered handler '''
    w = watch()
    # Increment call counter when called
    handle = lambda: w.call()
    # Register handler
    events.on("0")(handle)
    # Trigger handler
    run(events.trigger("0"))
    # Make sure we called once
    assert w.called


def test_trigger_multiple_calls(events, run, watch):
    ''' trigger calls re-registered handler twice '''
    w = watch()
    # Increment call counter when called
    handle = lambda: w.call()
    # Register handler twice
    events.on("0")(handle)
    events.on("0")(handle)
    # Trigger handler
    run(events.trigger("0"))
    # Make sure we called twice
    assert w.calls == 2


def test_trigger_multiple_handlers(events, run, watch):
    ''' trigger calls re-registered handler twice '''
    w1 = watch()
    w2 = watch()
    # Increment call counter when called
    handle1 = lambda: w1.call()
    handle2 = lambda: w2.call()
    # Register handler twice
    events.on("0")(handle1)
    events.on("0")(handle2)
    # Trigger handler
    run(events.trigger("0"))
    # Make sure we called each once
    assert w1.calls == 1
    assert w2.calls == 1


def test_trigger_no_handlers(events, run):
    ''' trigger an event with no handlers '''
    run(events.trigger("some event"))


def test_trigger_superset_params(events, run):
    ''' trigger an event with kwarg keys that aren't in event params '''
    params = {}

    def func(one, two):
        params["one"] = one
        params["two"] = two

    events.on("2")(func)

    kwargs = {"one": 1, "two": 2, "unused": "value"}
    run(events.trigger("2", **kwargs))

    assert params["one"] == 1
    assert params["two"] == 2


def test_trigger_subset_params(events, run):
    ''' trigger an event with missing kwargs pads with None '''
    params = {}

    def func(one, two):
        params["one"] = one
        params["two"] = two

    events.on("2")(func)

    kwargs = {"one": 1}
    run(events.trigger("2", **kwargs))

    assert params["one"] == 1
    assert params["two"] is None


def test_trigger_subset_params_with_defaults(events, run):
    ''' trigger an event with missing kwargs uses function defaults '''
    params = {}

    def func(one, two="default"):
        params["one"] = one
        params["two"] = two

    events.on("2")(func)

    kwargs = {"one": 1}
    run(events.trigger("2", **kwargs))

    assert params["one"] == 1
    assert params["two"] == "default"


# ===================
# Function binding
# ===================


def test_bound_method_of_instance(events, run):
    ''' verify bound methods are correctly inspected '''
    params = {}

    class Class(object):
        def method(self, one, two="default"):
            params["one"] = one
            params["two"] = two
    instance = Class()
    bound_method = instance.method
    events.on("2")(bound_method)

    kwargs = {"one": 1}
    run(events.trigger("2", **kwargs))

    assert params["one"] == 1
    assert params["two"] == "default"
