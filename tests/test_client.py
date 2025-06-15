import asyncio
import logging

import pytest
from bottom.client import Client, wait_for
from bottom.core import Protocol
from bottom.irc import _suggest_issue, rfc2812_log
from bottom.util import create_task

from tests.helpers.fns import busy_wait, recv_bytes


async def test_connect(client):
    create_task(client.connect())
    assert client._protocol is None
    await client.wait("CLIENT_CONNECT")


async def test_ping_pong(client, server):
    msg = "ping-message"

    @client.on("PING")
    async def pong(message, **kwargs):
        await client.send("pong", message=message[::-1])

    async def run():
        await client.connect()
        server.write(f"PING :{msg}")

    create_task(run())

    # empty until we yield execution with await below
    assert server.received == []

    # can't just await client.wait("PING") since we want to see the response
    # get to the server
    await busy_wait(lambda: server.received)
    assert server.received == [f"PONG :{msg[::-1]}"]


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
        await client.send("Unknown Command")


async def test_send_before_connect(client):
    """Sending before connected raises"""
    with pytest.raises(RuntimeError):
        await client.send("pong")
    assert client._protocol is None


async def test_send_after_disconnect(client, server):
    """Sending after disconnect does not invoke writer"""
    await client.connect()
    await client.send("pong")
    await busy_wait(lambda: server.received)
    assert server.received == ["PONG"]

    await client.disconnect()
    await busy_wait(lambda: client._protocol is None)
    with pytest.raises(RuntimeError):
        await client.send("quit")
    assert server.received == ["PONG"]


async def test_unpack_triggers_client(client, client_protocol):
    """protocol pushes messages to the client"""
    received = []

    @client.on("PRIVMSG")
    async def receive(nick, user, host, target, message, **kw):
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

    assert len(result) == 2
    assert {"__event__": "BAR"} in result
    assert {"__event__": "FOO"} in result


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

    assert result == [{"__event__": "BAR"}]


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

    assert len(result) == 2
    assert {"__event__": "BAR"} in result
    assert {"__event__": "FOO"} in result


@pytest.mark.parametrize("mode", ["first", "all"])
async def test_wait_for_nothing(mode, client):
    """wait_for(mode="all") returns when all events have triggered"""

    race = wait_for(client, [], mode=mode)
    assert asyncio.iscoroutine(race)
    result = await race
    assert result == []


async def test_unknown_logs_first_run(client: Client, caplog: pytest.LogCaptureFixture):
    """protocol pushes messages to the client"""
    command = "UNKNOWN-FOO-BAR"
    msg = f":nick!user@host {command} #target :this is message\n".encode(client._encoding)

    await client.connect()

    with caplog.at_level(level=logging.INFO):
        # nothing logged yet
        assert not caplog.records

        # first message sees full notice
        await recv_bytes(client, msg)
        [(logger_name, _, message)] = caplog.record_tuples
        assert logger_name == rfc2812_log.name
        assert command in message
        for line in _suggest_issue["extra_lines"]:
            assert line in message

        # second message sees only the command
        caplog.clear()
        await recv_bytes(client, msg)
        [(logger_name, _, message)] = caplog.record_tuples
        assert logger_name == rfc2812_log.name
        assert command in message
        for line in _suggest_issue["extra_lines"]:
            assert line not in message

    # disable_first_run_message


async def test_disable_first_run_logger(client: Client, caplog: pytest.LogCaptureFixture):
    """disabling the first run prevents log message"""
    command = "UNKNOWN-FOO-BAR"
    msg = f":nick!user@host {command} #target :this is message\n".encode(client._encoding)

    await client.connect()

    with caplog.at_level(level=logging.INFO):
        # nothing logged yet
        assert not caplog.records

        # import here so that we don't implicitly rely on import order for some logger configuration
        from bottom.irc import disable_first_run_message

        disable_first_run_message()

        # first message doesn't see notice
        await recv_bytes(client, msg)
        [(logger_name, _, message)] = caplog.record_tuples
        assert logger_name == rfc2812_log.name
        # should still see the log for unknown command
        assert command in message

        # ensure the for loop below is actually checking something
        assert len(_suggest_issue["extra_lines"]) > 0

        for line in _suggest_issue["extra_lines"]:
            assert line not in message


async def test_disable_rfc2812_logger(client: Client, caplog: pytest.LogCaptureFixture):
    """disabling the whole logger"""
    command = "UNKNOWN-FOO-BAR"
    msg = f":nick!user@host {command} #target :this is message\n".encode(client._encoding)

    await client.connect()

    with caplog.at_level(level=logging.INFO):
        # nothing logged yet
        assert not caplog.records

        assert rfc2812_log.disabled is False

        rfc2812_log.disabled = True

        # shouldn't see _anything_ here
        await recv_bytes(client, msg)
        assert not caplog.record_tuples
