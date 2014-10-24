from bottom import Connection


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


def test_send_strips(patch_connection, writer, events, run):
    ''' Send strips whitespace from string '''
    conn = Connection("host", "port", events, "UTF-8", True)
    run(conn.connect())
    conn.send("  a b  c | @#$ d  ")
    assert writer.used
    assert writer.has_written("a b  c | @#$ d\n")
