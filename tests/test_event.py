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
    return params.__getitem__


@pytest.fixture
def events(getparams, loop):
    return event.EventsMixin(getparams, loop=loop)


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
    for e in ["0", "1", "2"]:
        events.on(e)(lambda: None)


def test_on_all(events):
    ''' register a handler with all available parameters '''
    events.on("2")(lambda one, two: None)


def test_on_superset(events):
    ''' raise when handler expects unavailable parameters '''
    with pytest.raises(ValueError):
        events.on("1")(lambda one, two: None)


def test_on_ordering(events):
    ''' ordering is irrelevant '''
    events.on("2")(lambda two, one: None)


def test_with_kwargs(events):
    ''' kwargs is ok without masking '''
    events.on("2")(lambda one, **kwargs: None)


def test_with_kwargs_masking(events):
    ''' masking kwargs raise '''
    with pytest.raises(ValueError):
        events.on("2")(lambda one, **two: None)


def test_var_args(events):
    ''' *args are never ok '''
    with pytest.raises(ValueError):
        events.on("2")(lambda one, *args: None)


def test_defaults(events):
    ''' defaults are fine '''
    events.on("2")(lambda one="foo", two="bar": None)


def test_on_coroutine(events):
    ''' coroutines are fine '''
    handle = asyncio.coroutine(lambda one: None)
    events.on("1")(handle)


# ===================
# EventsMixin.trigger
# ===================

def test_trigger(events, watch, flush):
    ''' trigger calls registered handler '''
    w = watch()
    events.on("0")(lambda: w.call())
    events.trigger("0")
    flush()
    assert w.called


def test_trigger_multiple_calls(events, watch, flush):
    ''' trigger calls re-registered handler twice '''
    w = watch()
    events.on("0")(lambda: w.call())
    events.on("0")(lambda: w.call())
    events.trigger("0")
    flush()
    assert w.calls == 2


def test_trigger_multiple_handlers(events, watch, flush):
    ''' trigger calls re-registered handler twice '''
    w1 = watch()
    w2 = watch()
    events.on("0")(lambda: w1.call())
    events.on("0")(lambda: w2.call())
    events.trigger("0")
    flush()
    assert w1.calls == 1
    assert w2.calls == 1


def test_trigger_no_handlers(events, flush):
    ''' trigger an event with no handlers '''
    events.trigger("some event")
    flush()


def test_trigger_superset_params(events, flush):
    ''' trigger an event with kwarg keys that aren't in event params '''
    params = {}

    def func(one, two):
        params["one"] = one
        params["two"] = two
    events.on("2")(func)
    kwargs = {"one": 1, "two": 2, "unused": "value"}
    events.trigger("2", **kwargs)
    flush()
    assert params["one"] == 1
    assert params["two"] == 2


def test_trigger_subset_params(events, flush):
    ''' trigger an event with missing kwargs pads with None '''
    params = {}

    def func(one, two):
        params["one"] = one
        params["two"] = two
    events.on("2")(func)
    kwargs = {"one": 1}
    events.trigger("2", **kwargs)
    flush()
    assert params["one"] == 1
    assert params["two"] is None


def test_trigger_subset_params_with_defaults(events, flush):
    ''' trigger an event with missing kwargs uses function defaults '''
    params = {}

    def func(one, two="default"):
        params["one"] = one
        params["two"] = two
    events.on("2")(func)
    kwargs = {"one": 1}
    events.trigger("2", **kwargs)
    flush()
    assert params["one"] == 1
    assert params["two"] == "default"


# ===================
# Function binding
# ===================


def test_bound_method_of_instance(events, flush):
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
    events.trigger("2", **kwargs)
    flush()
    assert params["one"] == 1
    assert params["two"] == "default"


# ===================
# Ordering + Blocking
# ===================


def test_callback_ordering(events, flush, loop):
    ''' Callbacks for a second event don't queue behind the first event '''
    second_complete = asyncio.Event(loop=loop)
    call_order = []
    complete_order = []

    @asyncio.coroutine
    def first():
        call_order.append("first")
        yield from second_complete.wait()
        complete_order.append("first")

    @asyncio.coroutine
    def second():
        call_order.append("second")
        complete_order.append("second")
        second_complete.set()

    events.on("0")(first)
    events.on("0")(second)

    events.trigger("0")
    flush()
    assert call_order == ["first", "second"]
    assert complete_order == ["second", "first"]
