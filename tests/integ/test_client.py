import asyncio

from bottom.core import Protocol
from bottom.util import create_task

from tests.conftest import busy_wait


async def test_connect(client):
    create_task(client.connect())
    assert client.protocol is None
    await client.wait("CLIENT_CONNECT")


async def test_ping_pong(client, server):
    @client.on("PING")
    def pong(message, **kwargs):
        client.send("PONG", message=message[::-1])

    async def run():
        await client.connect()
        server.write("PING :ping-message")

    create_task(run())

    # empty until we yield execution with await below
    assert server.received == []

    # can't just await client.wait("PING") since we want to see the response
    # get to the server
    await busy_wait(lambda: server.received)
    assert server.received == ["PONG :egassem-gnip"]


async def test_multi_reconnect(client, client_protocol: Protocol):
    def expect(conns, disconns):
        assert client.triggers["CLIENT_CONNECT"] == conns
        assert client.triggers["CLIENT_DISCONNECT"] == disconns

    # initial state: client_protocol fixture connects before test starts
    expect(1, 0)

    # parallel connects cause no change; already connected
    await asyncio.gather(client.connect(), client.connect())
    expect(1, 0)

    # simulate lost conn from the protocol
    client_protocol.connection_lost(exc=None)
    expect(1, 1)

    # parallel connects only cause one connect.
    # NOTE: the slower coro's Protocol cleans up, but doesn't count as a client_disconnect.
    await asyncio.gather(client.connect(), client.connect())
    expect(2, 1)

    # subsequent disconnects don't trigger another disconnect
    await asyncio.gather(client.disconnect(), client.disconnect())
    expect(2, 2)

    # simulate stale protocol (from beginning of the test) closing again
    # this isn't associated with the client, so shouldn't count as client_disconnect.
    client_protocol.connection_lost(exc=None)
    expect(2, 2)
