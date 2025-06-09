import asyncio

from bottom.core import Protocol

from tests.conftest import busy_wait


async def test_protocol_write(client_protocol: Protocol, server):
    """Protocol strips and normalizes each write"""
    client_protocol.write("hello")
    client_protocol.write("world\r\n")
    client_protocol.write("\r\nfoo\r\n")

    # asyncio.sleep(0) isn't enough for transports to drain
    await busy_wait(lambda: len(server.received) >= 3)

    assert server.received == ["hello", "world", "foo"]


def test_partial_line(client, client_protocol: Protocol):
    """Part of an IRC line is sent across; shouldn't be emitted as an event"""
    client_protocol.data_received(b":nick!user@host PRIVMSG")
    assert b"PRIVMSG" in client_protocol.buffer
    assert not client.triggers["PRIVMSG"]


async def test_multipart_line(client, client_protocol):
    """Single line transmitted in multiple parts"""
    client_protocol.data_received(b":nick!user@host PRIVMSG")
    client_protocol.data_received(b" #target :this is message\r\n")
    await asyncio.sleep(0)
    assert client.triggers["PRIVMSG"] == 1


def test_multiline_chunk(client, client_protocol):
    """Multiple IRC lines in a single data_received block"""
    client_protocol.data_received(b":nick!user@host PRIVMSG #target :this is message\r\n" * 2)
    assert client.triggers["PRIVMSG"] == 2


def test_invalid_line(client, client_protocol):
    """Well-formatted but invalid line"""
    client_protocol.data_received(b"blah unknown command\r\n")
    # no rfc2812 events triggered
    assert list(client.triggers.keys()) == ["CLIENT_CONNECT"]


def test_close(client, client_protocol):
    """Protocol.close triggers connection_lost,
    client triggers exactly 1 disconnect"""
    client_protocol.close()
    assert client.triggers["CLIENT_DISCONNECT"] == 1
    assert client_protocol.closed

    client_protocol.close()
    assert client.triggers["CLIENT_DISCONNECT"] == 1

    client_protocol.transport.close()
    assert client.triggers["CLIENT_DISCONNECT"] == 1
