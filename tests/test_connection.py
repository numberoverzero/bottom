from bottom import Connection


def test_connect(patch_connection, writer, events, run):
    conn = Connection("host", "port", events, "UTF-8", True)
    run(conn.connect())
    assert conn.connected
    assert not writer.closed
    assert events.triggers("CLIENT_CONNECT") == 1


def test_connect_already_connected(patch_connection, writer, events, run):
    ''' Should only open_connection once, only one trigger '''
    conn = Connection("host", "port", events, "UTF-8", True)
    run(conn.connect())
    run(conn.connect())
    assert conn.connected
    assert not writer.closed
    assert events.triggers("CLIENT_CONNECT") == 1


def test_disconnect_before_connect(patch_connection, events, run):
    ''' Should not trigger '''
    conn = Connection("host", "port", events, "UTF-8", True)
    run(conn.disconnect())
    assert not conn.connected
    assert events.triggers("CLIENT_CONNECT") == 0
    assert events.triggers("CLIENT_DISCONNECT") == 0


def test_disconnect(writer, patch_connection, events, run):
    ''' Should only open_connection once, only one trigger '''
    conn = Connection("host", "port", events, "UTF-8", True)
    run(conn.connect())
    run(conn.disconnect())
    assert not conn.connected
    assert writer.closed
    assert events.triggers("CLIENT_CONNECT") == 1
    assert events.triggers("CLIENT_DISCONNECT") == 1


def test_disconnect_already_disconnected(patch_connection, events, run):
    ''' Should only open_connection once, only one trigger '''
    conn = Connection("host", "port", events, "UTF-8", True)
    run(conn.connect())
    run(conn.disconnect())
    run(conn.disconnect())
    assert not conn.connected
    assert events.triggers("CLIENT_CONNECT") == 1
    assert events.triggers("CLIENT_DISCONNECT") == 1
