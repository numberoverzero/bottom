def test_connect(client, connect):
    """Connect client triggers client_connect"""
    connect()
    assert client.triggers['CLIENT_CONNECT'] == 1


def test_ping_pong(client, server, connect, flush):
    connect()
    server.write("PING :ping-message")
    client.send("PONG")

    # Protocol doesn't advance until loop flushes
    assert not client.triggers["PING"]
    assert not server.received

    flush()

    # Both should have been received now
    assert client.triggers["PING"] == 1
    assert server.received == ["PONG"]
