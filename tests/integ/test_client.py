import asyncio

from bottom.core import Protocol
from bottom.util import create_task


async def test_connect(client):
    create_task(client.connect())
    assert client.protocol is None
    await client.wait("CLIENT_CONNECT")


async def test_ping_pong(client, server):
    async def run():
        await client.connect()
        server.write("PING :ping-message")
        client.send("PONG")

    create_task(run())

    # empty until we yield execution with await below
    assert server.received == []

    await client.wait("PING")
    assert server.received == ["PONG"]


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
