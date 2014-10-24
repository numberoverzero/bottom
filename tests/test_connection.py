from bottom import Connection
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
    assert events.triggers("CLIENT_CONNECT") == 1


def test_connect_already_connected(patch_connection, writer, events, run):
    ''' Does not trigger CLIENT_CONNECT multiple times '''
    conn = Connection("host", "port", events, "UTF-8", True)
    run(conn.connect())
    run(conn.connect())
    assert not writer.closed
    assert events.triggers("CLIENT_CONNECT") == 1


def test_disconnect_before_connect(patch_connection, events, run):
    ''' disconnect before connect does nothing '''
    conn = Connection("host", "port", events, "UTF-8", True)
    run(conn.disconnect())
    assert not conn.connected
    assert events.triggers("CLIENT_CONNECT") == 0
    assert events.triggers("CLIENT_DISCONNECT") == 0


def test_disconnect(writer, patch_connection, events, run):
    ''' Connection.disconnect closes writer, triggers CLIENT_DISCONNECT '''
    conn = Connection("host", "port", events, "UTF-8", True)
    run(conn.connect())
    run(conn.disconnect())
    assert not conn.connected
    assert writer.closed
    assert conn.writer is None
    assert events.triggers("CLIENT_CONNECT") == 1
    assert events.triggers("CLIENT_DISCONNECT") == 1


def test_disconnect_already_disconnected(patch_connection, events, run):
    ''' Does not trigger CLIENT_DISCONNECT multiple times '''
    conn = Connection("host", "port", events, "UTF-8", True)
    run(conn.connect())
    run(conn.disconnect())
    run(conn.disconnect())
    assert events.triggers("CLIENT_CONNECT") == 1
    assert events.triggers("CLIENT_DISCONNECT") == 1


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
