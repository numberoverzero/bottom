import pytest
from bottom.plugins.router import Router


@pytest.fixture
def router(client):
    return Router(client)


def test_router_registers_callback(router, client, flush):
    called = False
    name = "foo"
    message = "test {}".format(name)
    expected_nick = "nick"
    expected_target = "target"

    @router.route("test [name]")
    def handle(nick, target, fields):
        assert nick == expected_nick
        assert target == expected_target
        assert fields["name"] == name

        nonlocal called
        called = True

    client.trigger("privmsg", nick=expected_nick,
                   target=expected_target, message=message)
    flush()

    assert called


def test_decorator_returns_original(router):
    def original_func(nick, target, fields):
        pass

    wrapped_func = router.route("pattern")(original_func)
    assert wrapped_func is original_func


def test_handle_no_routes(router, flush):
    router._handle("nick", "target", "message")
    flush()


def test_handle_no_matching_route(router, flush):
    @router.route("hello, [name]")
    async def handle(nick, target, fields):
        # Should not be called
        assert False

    router._handle("nick", "target", "does not match")
    flush()


def test_handle_with_matching_route(router, flush):
    names = []

    @router.route("hello, [name]")
    def handle(nick, target, fields):
        names.append(fields['name'])

    router._handle("nick", "target", "hello, jack")
    router._handle("nick", "target", "hello, hello, recursion")
    flush()

    assert ["jack", "hello, recursion"] == names


def test_back_reference(router, flush):
    expected = {"field": "some value here", "tag": "element"}

    @router.route("<[tag]>[field]</[:ref(tag)]>")
    def handle(nick, target, fields):
        assert fields == expected

    router._handle("nick", "target", "<element>some value here</element>")
    flush()
