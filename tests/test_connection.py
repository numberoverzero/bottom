from bottom.connection import Connection
import pytest


@pytest.fixture
def conn(patch_connection, events, run):
    ''' Generic connection that is ready to read/send '''
    conn = Connection("host", "port", events, "UTF-8", True)
    run(conn.connect())
    assert conn.connected
    return conn


def test_connect(patch_connection, writer, events, run):
    ''' Connection.Connect opens a writer, triggers CLIENT_CONNECT '''
    conn = Connection("host", "port", events, "UTF-8", True)
    run(conn.connect())
    assert conn.connected
    assert not writer.closed
    assert events.triggered("CLIENT_CONNECT")


def test_connect_already_connected(patch_connection, writer, events, run):
    ''' Does not trigger CLIENT_CONNECT multiple times '''
    conn = Connection("host", "port", events, "UTF-8", True)
    run(conn.connect())
    run(conn.connect())
    assert not writer.closed
    assert events.triggered("CLIENT_CONNECT")


def test_disconnect_before_connect(patch_connection, events, run):
    ''' disconnect before connect does nothing '''
    conn = Connection("host", "port", events, "UTF-8", True)
    run(conn.disconnect())
    assert not conn.connected
    assert not events.triggered("CLIENT_CONNECT")
    assert not events.triggered("CLIENT_DISCONNECT")


def test_disconnect(writer, patch_connection, events, run):
    ''' Connection.disconnect closes writer, triggers CLIENT_DISCONNECT '''
    conn = Connection("host", "port", events, "UTF-8", True)
    run(conn.connect())
    run(conn.disconnect())
    assert not conn.connected
    assert writer.closed
    assert conn.writer is None
    assert events.triggered("CLIENT_CONNECT")
    assert events.triggered("CLIENT_DISCONNECT")


def test_disconnect_already_disconnected(patch_connection, events, run):
    ''' Does not trigger CLIENT_DISCONNECT multiple times '''
    conn = Connection("host", "port", events, "UTF-8", True)
    run(conn.connect())
    run(conn.disconnect())
    run(conn.disconnect())
    assert events.triggered("CLIENT_CONNECT")
    assert events.triggered("CLIENT_DISCONNECT")


def test_send_before_connected(patch_connection, writer, events, run):
    ''' Nothing happens when sending before connecting '''
    conn = Connection("host", "port", events, "UTF-8", True)
    assert not conn.connected
    conn.send("test")
    assert not writer.used


def test_send_disconnected(patch_connection, writer, events, run):
    ''' Nothing happens when sending after disconnecting '''
    conn = Connection("host", "port", events, "UTF-8", True)
    run(conn.connect())
    run(conn.disconnect())
    conn.send("test")
    assert not writer.used


def test_send_strips(conn, writer):
    ''' Send strips whitespace from string '''
    conn.send("  a b  c | @#$ d  ")
    assert writer.used
    assert writer.has_written("a b  c | @#$ d\n")


def test_read_before_connected(patch_connection, reader, events, run):
    ''' Nothing happens when reading before connecting '''
    conn = Connection("host", "port", events, "UTF-8", True)
    value = run(conn.read())
    assert not value
    assert not reader.used


def test_read_disconnected(patch_connection, reader, events, run):
    ''' Nothing happens when reading after disconnecting '''
    conn = Connection("host", "port", events, "UTF-8", True)
    run(conn.connect())
    run(conn.disconnect())
    value = run(conn.read())
    assert not value
    assert not reader.used


def test_read_eoferror(conn, reader, run):
    ''' Nothing to read '''
    value = run(conn.read())
    assert not value
    assert reader.used


def test_read_strips(conn, reader, run):
    ''' newline and space characters are stripped off '''
    reader.push("  a b  c | @#$ d  \n")
    value = run(conn.read())
    assert value == "a b  c | @#$ d"
    assert reader.has_read("  a b  c | @#$ d  \n")


def test_run_without_message(conn, events, run):
    ''' Connection.run should connect, read empty, disconnect, return '''
    run(conn.run())
    assert events.triggered("CLIENT_CONNECT")
    assert events.triggered("CLIENT_DISCONNECT")


def test_run_trigger_command(conn, reader, events, eventparams, run):
    eventparams["PRIVMSG"] = ["nick", "user", "host", "target", "message"]
    reader.push(":nick!user@host PRIVMSG #target :this is message")
    received = []

    @events.on("PRIVMSG")
    def receive(nick, user, host, target, message):
        received.extend([nick, user, host, target, message])

    run(conn.run())

    assert reader.has_read(":nick!user@host PRIVMSG #target :this is message")
    assert events.triggered("PRIVMSG")
    assert received == ["nick", "user", "host", "#target", "this is message"]


def test_run_trigger_unknown_command(conn, reader, events, run):
    reader.push("unknown_command")
    run(conn.run())

    assert reader.has_read("unknown_command")
    assert not events.triggered("unknown_command")
