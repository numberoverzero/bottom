import pytest
from bottom import Client
from bottom.plugins.router import Router


class MockConnection():
    def __init__(self, *a, **kw):
        pass


class MockClient(Client):
        __conn_cls__ = MockConnection

        def __init__(self, *args, **kwargs):
            self.handlers = []
            super().__init__(*args, **kwargs)

        def on(self, command):
            def wrap(function):
                self.handlers.append((command, function))
                return function
            return wrap


@pytest.fixture
def client():
    return MockClient("host", "port")


@pytest.fixture
def router(client):
    return Router(client)


def test_init_registers_privmsg(client):
    router = Router(client)
    assert ("PRIVMSG", router.handle) in client.handlers


def test_decorator_returns_original(router):
    def original_func(nick, target, fields):
        pass

    wrapped_func = router.route("pattern")(original_func)
    assert wrapped_func is original_func


def test_handle_no_routes(router, loop):
    loop.run_until_complete(
        router.handle("nick", "target", "message"))


def test_handle_no_matching_route(router, loop):
    @router.route("hello, [name]")
    def handle(nick, target, fields):
        # Should not be called
        assert False

    loop.run_until_complete(
        router.handle("nick", "target", "does not match"))


def test_handle_with_matching_route(router, loop):
    names = []

    @router.route("hello, [name]")
    def handle(nick, target, fields):
        names.append(fields['name'])

    loop.run_until_complete(
        router.handle("nick", "target", "hello, jack"))
    loop.run_until_complete(
        router.handle("nick", "target", "hello, hello, recursion"))

    assert ["jack", "hello, recursion"] == names


def test_back_reference(router, loop):
    actual_fields = {}

    @router.route("<[tag]>[field]</[:ref(tag)]>")
    def handle(nick, target, fields):
        actual_fields.update(fields)

    loop.run_until_complete(
        router.handle("nick", "target", "<element>some value here</element>"))
    assert {"field": "some value here", "tag": "element"} == actual_fields
