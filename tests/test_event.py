import asyncio


def test_on_signature(events):
    ''' register a handler with full function signature options'''
    events.on("f")(lambda arg, *args, kw_only, kw_default="d", **kwargs: None)


def test_on_coroutine(events):
    async def handle(arg, *args, kw_only, kw_default="d", **kwargs):
        pass
    events.on("f")(handle)


def test_trigger_no_handlers(events, flush):
    ''' trigger an event with no handlers '''
    events.trigger("some event")
    flush()


def test_trigger_one_handler(events, watch, flush):
    events.on("f")(lambda: watch.call())
    events.trigger("f")
    flush()
    assert events.triggered("f")
    assert watch.called


def test_trigger_multiple_handlers(events, flush):
    h1, h2 = 0, 0

    def incr(first=True):
        nonlocal h1, h2
        if first:
            h1 += 1
        else:
            h2 += 1

    events.on("f")(lambda: incr(first=True))
    events.on("f")(lambda: incr(first=False))
    events.trigger("f")
    flush()
    assert h1 == 1
    assert h2 == 1


def test_trigger_unpacking(events, flush):
    """ Usual semantics for unpacking **kwargs """
    called = False

    def func(arg, *args, kw_only, kw_default="default", **kwargs):
        nonlocal called
        assert arg == "arg"
        assert not args
        assert kw_only == "kw_only"
        assert kw_default == "default"
        assert kwargs["extra"] == "extra"
        called = True

    events.on("f")(func)
    events.trigger("f", **{s: s for s in ["arg", "kw_only", "extra"]})
    flush()
    assert called


def test_bound_method_of_instance(events, flush):
    ''' verify bound methods are correctly inspected '''
    class Class(object):
        def method(self, arg, kw_default="default"):
            assert arg == "arg"
            assert kw_default == "default"
    instance = Class()

    events.on("f")(instance.method)
    events.trigger("f", **{"arg": "arg"})
    flush()


def test_callback_ordering(events, flush, loop):
    ''' Callbacks for a second event don't queue behind the first event '''
    second_complete = asyncio.Event(loop=loop)
    call_order = []
    complete_order = []

    async def first():
        call_order.append("first")
        await second_complete.wait()
        complete_order.append("first")

    async def second():
        call_order.append("second")
        complete_order.append("second")
        second_complete.set()

    events.on("f")(first)
    events.on("f")(second)

    events.trigger("f")
    flush()
    assert call_order == ["first", "second"]
    assert complete_order == ["second", "first"]
