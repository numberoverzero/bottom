def test_connect(connection, events, writer, schedule, flush):
    ''' Connection.Connect opens a writer, triggers CLIENT_CONNECT '''
    schedule(connection.connect())
    flush()
    assert connection.connected
    assert not writer.closed
    assert events.triggered("CLIENT_CONNECT")


def test_already_connected(connection, events, writer, schedule, flush):
    ''' Does not trigger CLIENT_CONNECT multiple times '''
    schedule(connection.connect(), connection.connect())
    flush()
    assert not writer.closed
    assert events.triggered("CLIENT_CONNECT")


def test_disconnect_before_connect(connection, events, schedule, flush):
    ''' disconnect before connect does nothing '''
    schedule(connection.disconnect())
    flush()
    assert not connection.connected
    assert not events.triggered("CLIENT_CONNECT")
    assert not events.triggered("CLIENT_DISCONNECT")


def test_disconnect(writer, patch_connection, events, connection,
                    schedule, flush):
    ''' Connection.disconnect closes writer, triggers CLIENT_DISCONNECT '''
    schedule(connection.connect(), connection.disconnect())
    flush()
    assert not connection.connected
    assert writer.closed
    assert connection.writer is None
    assert events.triggered("CLIENT_CONNECT")
    assert events.triggered("CLIENT_DISCONNECT")


def test_already_disconnected(connection, events, schedule, flush):
    ''' Does not trigger CLIENT_DISCONNECT multiple times '''
    schedule(connection.connect(),
             connection.disconnect(),
             connection.disconnect())
    flush()
    assert events.triggered("CLIENT_CONNECT")
    assert events.triggered("CLIENT_DISCONNECT")


def test_send_before_connected(connection, writer):
    ''' Nothing happens when sending before connecting '''
    assert not connection.connected
    connection.send("test")
    assert not writer.used


def test_send_disconnected(connection, writer, schedule, flush):
    ''' Nothing happens when sending after disconnecting '''
    schedule(connection.connect(), connection.disconnect())
    flush()
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


def test_read_disconnected(connection, reader, schedule, flush, loop):
    ''' Nothing happens when reading after disconnecting '''
    schedule(connection.connect(), connection.disconnect())
    flush()
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


def test_run_without_message(connection, events, loop):
    ''' Connection.run should connect, read empty, disconnect, return '''
    loop.run_until_complete(connection.run())
    assert events.triggered("CLIENT_CONNECT")
    assert events.triggered("CLIENT_DISCONNECT")


def test_run_trigger_command(connection, reader, events, eventparams, loop):
    eventparams["PRIVMSG"] = ["nick", "user", "host", "target", "message"]
    reader.push(":nick!user@host PRIVMSG #target :this is message")
    received = []

    @events.on("PRIVMSG")
    def receive(nick, user, host, target, message):
        received.extend([nick, user, host, target, message])

    loop.run_until_complete(connection.run())
    assert reader.has_read(":nick!user@host PRIVMSG #target :this is message")
    assert events.triggered("PRIVMSG")
    assert received == ["nick", "user", "host", "#target", "this is message"]


def test_run_trigger_unknown_command(connection, reader, events, loop):
    reader.push("unknown_command")
    loop.run_until_complete(connection.run())

    assert reader.has_read("unknown_command")
    assert not events.triggered("unknown_command")
