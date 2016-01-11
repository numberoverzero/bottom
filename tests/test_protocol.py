from bottom.protocol import Protocol


def test_connect(protocol, transport, client):
    protocol.connection_made(transport)
    assert client.triggers["CLIENT_CONNECT"] == 1


def test_disconnect_before_connect(protocol, transport, client):
    protocol.connection_lost(transport)
    assert client.triggers["CLIENT_DISCONNECT"] == 1


def test_disconnect_after_connect(protocol, transport, client):
    protocol.connection_made(transport)
    protocol.connection_lost(transport)
    assert client.triggers["CLIENT_CONNECT"] == 1
    assert client.triggers["CLIENT_DISCONNECT"] == 1
    assert transport.closed


def test_write(protocol, transport):
    protocol.connection_made(transport)
    protocol.write("hello")
    protocol.write("world\r\n")
    protocol.write("\r\nfoo\r\n")
    assert transport.written == [b"hello\r\n", b"world\r\n", b"\r\nfoo\r\n"]


def test_partial_line(protocol, transport, client):
    """Part of an IRC line is sent across; shouldn't be emitted as an event"""
    protocol.data_received(b":nick!user@host PRIVMSG")
    assert not client.triggers["PRIVMSG"]


def test_multipart_line(protocol, transport, client):
    """Single line transmitted in multiple parts"""
    protocol.data_received(b":nick!user@host PRIVMSG")
    protocol.data_received(b" #target :this is message\r\n")
    assert client.triggers["PRIVMSG"] == 1


def test_multiline_chunk(protocol, transport, client):
    """Multiple IRC lines in a single data_received block"""
    protocol.data_received(
        b":nick!user@host PRIVMSG #target :this is message\r\n" * 2)
    assert client.triggers["PRIVMSG"] == 2


def test_invalid_line(protocol, transport, client):
    """Well-formatted but invalid line"""
    protocol.data_received(b"blah unknown command\r\n")
    assert not client.triggers


def test_factory(client):
    """Protocol.factory returns a function that is
    suitable for loop.create_connection, with a reference to the client"""
    factory = Protocol.factory(client)
    for _ in range(10):
        assert factory().client is client
