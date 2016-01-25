def test_connect(client, connect):
    """Connect client triggers client_connect"""
    connect()
    assert client.triggers['CLIENT_CONNECT'] == 1


def test_ping_pong(client, server, connect, flush):
    connect()
    server.write("PING :ping-message")
    client.send("PONG")

    # Even though the server writes the message immediately, the client
    # doesn't receive the PING until a flush.
    assert not client.triggers["PING"]
    assert not server.received

    # After the first flush the client has received the full PING.  However,
    # the PONG `send` requires another flush.  The first flush here will
    # only kick off the async _send, not clear the buffer to the server.
    flush()
    assert client.triggers["PING"] == 1
    assert not server.received

    # The client clears the outgoing buffer, and the PONG finally makes it to
    # the server's protocol and is unpacked.
    flush()
    assert client.triggers["PING"] == 1
    assert server.received == ["PONG"]
