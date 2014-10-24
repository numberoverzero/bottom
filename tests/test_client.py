from bottom import Client
import pytest


@pytest.fixture
def client(patch_connection, run):
    '''
    Return a client with mocked out asyncio.

    Pulling in patch_connection here mocks out asyncio.open_connection,
    so that we can use reader, writer, run in tests.
    '''
    return Client("host", "port")


def test_send_unknown_command(client, run):
    ''' Sending an unknown command raises '''
    run(client.connect())
    assert client.connected
    with pytest.raises(ValueError):
        client.send("Unknown_Command")


def test_send_before_connected(client, writer, run):
    ''' Sending before connected does not invoke writer '''
    client.send("PONG")
    assert not writer.used


def test_send_after_disconnected(client, writer, run):
    ''' Sending after disconnect does not invoke writer '''
    run(client.connect())
    run(client.disconnect())
    client.send("PONG")
    assert not writer.used


def test_on(client):
    ''' Client.on corrects case, throws on unknown events '''

    @client.on('privmsg')
    def route(nick, target, message):
        pass
    assert len(client.__partials__["PRIVMSG"]) == 1

    with pytest.raises(ValueError):
        client.on("UNKNOWN_COMMAND")(route)


def test_run_(client, reader, eventparams, run):
    ''' run delegates to Connection, which triggers events on the Client '''
    reader.push(":nick!user@host PRIVMSG #target :this is message")
    received = []

    @client.on("PRIVMSG")
    def receive(nick, user, host, target, message):
        received.extend([nick, user, host, target, message])

    run(client.run())

    assert reader.has_read(":nick!user@host PRIVMSG #target :this is message")
    assert received == ["nick", "user", "host", "#target", "this is message"]
