async def test_connect(client):
    """Connect client triggers client_connect"""
    await client.connect()
    assert client.triggers["CLIENT_CONNECT"] == 1


async def test_ping_pong(client, server):
    await client.connect()

    server.write("PING :ping-message")
    client.send("PONG")

    # Protocol doesn't advance until loop flushes
    assert not client.triggers["PING"]
    assert server.received == []

    # yield execution
    await client.wait("PING")

    # Both should have been received now
    assert client.triggers["PING"] == 1
    assert server.received == ["PONG"]
