def test_connect(connection, client, writer, schedule):
    ''' Connection.Connect opens a writer, triggers CLIENT_CONNECT '''
    schedule(connection.connect())
    assert connection.connected
    assert not writer.closed
    assert client.triggers["CLIENT_CONNECT"] == 1


def test_already_connected(connection, client, writer, schedule):
    ''' Does not trigger CLIENT_CONNECT multiple times '''
    schedule(connection.connect(), connection.connect())
    assert not writer.closed
    assert client.triggers["CLIENT_CONNECT"] == 1


def test_disconnect_before_connect(connection, client, schedule):
    ''' disconnect before connect does nothing '''
    schedule(connection.disconnect())
    assert not connection.connected
    assert not client.triggers["CLIENT_CONNECT"] == 1
    assert not client.triggers["CLIENT_DISCONNECT"] == 1


def test_disconnect(writer, patch_connection, client, connection,
                    schedule):
    ''' Connection.disconnect closes writer, triggers CLIENT_DISCONNECT '''
    schedule(connection.connect(), connection.disconnect())
    assert not connection.connected
    assert writer.closed
    assert connection.writer is None
    assert client.triggers["CLIENT_CONNECT"] == 1
    assert client.triggers["CLIENT_DISCONNECT"] == 1


def test_already_disconnected(connection, client, schedule):
    ''' Does not trigger CLIENT_DISCONNECT multiple times '''
    schedule(connection.connect(),
             connection.disconnect(),
             connection.disconnect())
    assert client.triggers["CLIENT_CONNECT"] == 1
    assert client.triggers["CLIENT_DISCONNECT"] == 1


def test_send_before_connected(connection, writer):
    ''' Nothing happens when sending before connecting '''
    assert not connection.connected
    connection.send("test")
    assert not writer.used


def test_send_disconnected(connection, writer, schedule):
    ''' Nothing happens when sending after disconnecting '''
    schedule(connection.connect(), connection.disconnect())
    connection.send("test")
    assert not writer.used


def test_send_strips(connection, writer, loop):
    ''' Send strips whitespace from string '''
    loop.run_until_complete(connection.connect())
    connection.send("  a b  c | @#$ d  ")
    assert writer.used
    assert writer.has_written("a b  c | @#$ d\n")


def test_read_before_connected(connection, reader, loop):
    ''' Nothing happens when reading before connecting '''
    value = loop.run_until_complete(connection.read())
    assert not value
    assert not reader.used


def test_read_disconnected(connection, reader, schedule, loop):
    ''' Nothing happens when reading after disconnecting '''
    schedule(connection.connect(), connection.disconnect())
    value = loop.run_until_complete(connection.read())
    assert not value
    assert not reader.used


def test_read_eoferror(connection, reader, loop):
    ''' Nothing to read '''
    loop.run_until_complete(connection.connect())
    value = loop.run_until_complete(connection.read())
    assert not value
    assert reader.used


def test_read_strips(connection, reader, loop):
    ''' newline and space characters are stripped off '''
    reader.push("  a b  c | @#$ d  \n")
    loop.run_until_complete(connection.connect())
    value = loop.run_until_complete(connection.read())
    assert value == "a b  c | @#$ d"
    assert reader.has_read("  a b  c | @#$ d  \n")


def test_run_without_message(connection, client, loop):
    ''' Connection.run should connect, read empty, disconnect, return '''
    loop.run_until_complete(connection.run())
    assert client.triggers["CLIENT_CONNECT"] == 1
    assert client.triggers["CLIENT_DISCONNECT"] == 1


def test_run_trigger_command(connection, reader, client, loop):
    reader.push(":nick!user@host PRIVMSG #target :this is message")
    received = []

    @client.on("PRIVMSG")
    def receive(nick, user, host, target, message):
        received.extend([nick, user, host, target, message])

    loop.run_until_complete(connection.run())
    assert reader.has_read(":nick!user@host PRIVMSG #target :this is message")
    assert client.triggers["PRIVMSG"] == 1
    assert received == ["nick", "user", "host", "#target", "this is message"]


def test_run_trigger_unknown_command(connection, reader, client, loop):
    reader.push("unknown_command")
    loop.run_until_complete(connection.run())

    assert reader.has_read("unknown_command")
    assert client.triggers["unknown_command"] == 0
