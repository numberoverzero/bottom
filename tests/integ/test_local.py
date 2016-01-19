def test_connect(client, connect):
    """Connect client triggers client_connect"""
    connect()
    assert client.triggers['CLIENT_CONNECT'] == 1


def test_ping_pong(client, server, connect, waiter):
    mark, wait = waiter()

    @client.on("PING")
    def handle(**kwargs):
        assert kwargs == {"message": "ping-message"}
        client.send("PONG")
        mark()

    connect()
    server.write("PING :ping-message")
    wait()
    assert server.received == ["PONG"]
