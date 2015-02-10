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


def test_init_registers_privmsg(client):
    router = Router(client)
    assert ("PRIVMSG", router.handle) in client.handlers
