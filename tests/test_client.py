import asyncio

import pytest
from bottom.client import wait_for
from bottom.core import Protocol
from bottom.util import create_task

from tests.conftest import busy_wait


async def test_connect(client):
    create_task(client.connect())
    assert client._protocol is None
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


async def test_send_unknown_command(client):
    """Sending an unknown command raises"""
    with pytest.raises(ValueError):
        client.send("Unknown Command")


async def test_send_before_connect(client):
    """Sending before connected raises"""
    with pytest.raises(RuntimeError):
        client.send("PONG")
    assert client._protocol is None


async def test_send_after_disconnect(client, server):
    """Sending after disconnect does not invoke writer"""
    await client.connect()
    client.send("PONG")
    await busy_wait(lambda: server.received)
    assert server.received == ["PONG"]

    await client.disconnect()
    await busy_wait(lambda: client._protocol is None)
    with pytest.raises(RuntimeError):
        client.send("QUIT")
    assert server.received == ["PONG"]


async def test_unpack_triggers_client(client, client_protocol):
    """protocol pushes messages to the client"""
    received = []

    @client.on("PRIVMSG")
    async def receive(nick, user, host, target, message):
        received.extend([nick, user, host, target, message])

    client_protocol.data_received(b":nick!user@host PRIVMSG #target :this is message\n")
    await busy_wait(lambda: received)
    assert received == ["nick", "user", "host", "#target", "this is message"]


async def test_wait_for_first_tie(client):
    """
    wait_for(mode="first") returns the event that triggered first, and cancels the others

    when more than one is set in the same loop tick, all completed triggers return.
    """

    race = wait_for(client, ["bar", "foo"], mode="first")
    client.trigger("foo")
    client.trigger("bar")
    result = await race

    assert set(result) == set(["foo", "bar"])


async def test_wait_for_first_single(client):
    """
    wait_for(mode="first") returns the event that triggered first, and cancels the others

    when more than one is set in the same loop tick, all completed triggers return.
    """

    async def slower():
        # this sleep staggers the "foo" trigger into the next cycle
        await asyncio.sleep(0)
        client.trigger("foo")

    race = wait_for(client, ["bar", "foo"], mode="first")
    client.trigger("bar")
    create_task(slower())
    result = await race

    assert result == ["bar"]


async def test_wait_for_all(client):
    """wait_for(mode="all") returns when all events have triggered"""

    async def slower():
        # this sleep staggers the "foo" trigger into the next cycle
        await asyncio.sleep(0)
        client.trigger("foo")

    race = wait_for(client, ["bar", "foo"], mode="all")
    client.trigger("bar")
    create_task(slower())
    result = await race

    assert set(result) == set(["foo", "bar"])


@pytest.mark.parametrize("mode", ["first", "all"])
async def test_wait_for_nothing(mode, client):
    """wait_for(mode="all") returns when all events have triggered"""

    race = wait_for(client, [], mode=mode)
    assert asyncio.iscoroutine(race)
    result = await race
    assert result == []
