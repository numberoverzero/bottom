def test_connection_made(protocol, transport):
    protocol.connection_made(transport)
    assert protocol.transport is transport


def test_connection_lost(protocol):
    class MockClient:
        called = False

        def _connection_lost(self, protocol):
            self.called = True

    protocol.client = client = MockClient()
    protocol.connection_lost(exc=None)
    assert client.called


def test_disconnect_after_connect(protocol, transport, active_client):
    assert active_client.triggers["CLIENT_CONNECT"] == 1

    # Don't need to check transport.closed since this is
    # only called when the transport is already closed
    protocol.connection_lost(exc=None)
    assert active_client.triggers["CLIENT_DISCONNECT"] == 1


def test_write(protocol, transport, active_client):
    protocol.write("hello")
    protocol.write("world\r\n")
    protocol.write("\r\nfoo\r\n")
    assert transport.written == [b"hello\r\n", b"world\r\n", b"foo\r\n"]


def test_partial_line(protocol, transport, active_client, flush):
    """Part of an IRC line is sent across; shouldn't be emitted as an event"""
    protocol.data_received(b":nick!user@host PRIVMSG")
    flush()
    assert not active_client.triggers["PRIVMSG"]


def test_multipart_line(protocol, transport, active_client, flush):
    """Single line transmitted in multiple parts"""
    protocol.data_received(b":nick!user@host PRIVMSG")
    protocol.data_received(b" #target :this is message\r\n")
    flush()
    assert active_client.triggers["PRIVMSG"] == 1


def test_multiline_chunk(protocol, transport, active_client, flush):
    """Multiple IRC lines in a single data_received block"""
    protocol.data_received(b":nick!user@host PRIVMSG #target :this is message\r\n" * 2)
    flush()
    assert active_client.triggers["PRIVMSG"] == 2


def test_invalid_line(protocol, transport, active_client, flush):
    """Well-formatted but invalid line"""
    protocol.data_received(b"blah unknown command\r\n")
    flush()
    assert list(active_client.triggers.keys()) == ["CLIENT_CONNECT"]


def test_close(protocol, transport, active_client):
    """Protocol.close triggers connection_lost,
    client triggers exactly 1 disconnect"""
    protocol.close()
    assert active_client.triggers["CLIENT_DISCONNECT"] == 1
    assert protocol.closed

    protocol.close()
    assert active_client.triggers["CLIENT_DISCONNECT"] == 1

    transport.close()
    assert active_client.triggers["CLIENT_DISCONNECT"] == 1
