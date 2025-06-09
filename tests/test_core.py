import asyncio

import pytest
from bottom.core import Protocol
from bottom.util import create_task, join_tasks

from tests.conftest import busy_wait


async def test_multiple_connect_protocol(client_protocol):
    """connecting a protocol more than once, even to the same transport, raises"""
    assert client_protocol.transport
    with pytest.raises(RuntimeError):
        client_protocol.connection_made(client_protocol.transport)


async def test_multiple_disconnect_protocol(client, client_protocol):
    """disconnecting a protocol more than once only triggers on_connection_lost once"""
    assert client_protocol.transport
    assert client.protocol is client_protocol
    assert client.triggers["CLIENT_DISCONNECT"] == 0

    client_protocol.connection_lost(None)
    assert client.protocol is None
    assert client_protocol.transport is None
    assert client.triggers["CLIENT_DISCONNECT"] == 1

    client_protocol.connection_lost(None)
    assert client.triggers["CLIENT_DISCONNECT"] == 1


async def test_write_disconnect_protocol(client, client_protocol):
    """can't write to a protocol after disconnecting it"""
    client_protocol.connection_lost(None)
    with pytest.raises(RuntimeError):
        client_protocol.write("PING")


async def test_multiple_close_protocol(client, client_protocol):
    """closing a protocol more than once only triggers on_connection_lost once"""
    client_protocol.close()
    # note: nothing's closed yet, because this calls into transport.close and
    # transport.close schedules its call to connection_lost on the event loop
    assert client.triggers["CLIENT_DISCONNECT"] == 0
    assert client_protocol.transport is not None
    assert client.protocol is client_protocol

    await asyncio.sleep(0)
    assert client.triggers["CLIENT_DISCONNECT"] == 1
    assert client_protocol.transport is None
    assert client.protocol is None

    client_protocol.close()
    await asyncio.sleep(0)
    assert client.triggers["CLIENT_DISCONNECT"] == 1
    assert client_protocol.transport is None
    assert client.protocol is None


async def test_no_handlers(client, client_protocol):
    """default handler is used when message_handlers stack is empty"""
    client.message_handlers.clear()
    client_protocol.data_received(b"world\r\n")
    assert len(asyncio.all_tasks()) == 2  # this test is asyncio.current_task

    # because there are no handlers, the stack processor will clear immediately
    await asyncio.sleep(0)
    assert list(asyncio.all_tasks()) == [asyncio.current_task()]


async def test_protocol_write(client_protocol: Protocol, server):
    """Protocol strips and normalizes each write"""
    client_protocol.write("hello")
    client_protocol.write("world\r\n")
    client_protocol.write("\r\nfoo\r\n")

    # asyncio.sleep(0) isn't enough for transports to drain
    await busy_wait(lambda: len(server.received) >= 3)

    assert server.received == ["hello", "world", "foo"]


async def test_partial_line(client_protocol: Protocol, captured_messages: list[str]):
    """partial IRC lines are not emitted to message_handlers"""
    client_protocol.data_received(b":nick!user@host PRIVMSG")
    # no pending writes/triggers
    assert list(asyncio.all_tasks()) == [asyncio.current_task()]

    assert b"PRIVMSG" in client_protocol.buffer
    assert not captured_messages

    client_protocol.data_received(b"\r\n")
    assert b"PRIVMSG" not in client_protocol.buffer
    # it's left the buffer but we need to yield execution so the message_handler stack runs
    await busy_wait(lambda: captured_messages)
    assert captured_messages == [":nick!user@host PRIVMSG"]


async def test_multipart_line(client_protocol: Protocol, captured_messages: list[str]):
    """Single line transmitted in multiple parts"""
    part1 = ":nick!user@host PRIVMSG"
    part2 = " #target :this is message"
    client_protocol.data_received(part1.encode())
    client_protocol.data_received(f"{part2}\r\n".encode())

    await busy_wait(lambda: captured_messages)
    assert captured_messages == [part1 + part2]


async def test_multiline_chunk(client_protocol: Protocol, captured_messages: list[str]):
    """Multiple IRC lines in a single data_received block"""
    privmsg = ":nick!user@host PRIVMSG #target :this is message"
    notice = ":n!u@h NOTICE #t :m"
    client_protocol.data_received(f"{privmsg}\r\n{notice}\r\n".encode())
    await busy_wait(lambda: captured_messages)
    assert captured_messages == [privmsg, notice]


async def test_invalid_line(client_protocol: Protocol, captured_messages: list[str]):
    """Well-formatted but invalid line"""
    invalid_line = "blah unknown command"
    client_protocol.data_received(f"{invalid_line}\r\n".encode())

    await busy_wait(lambda: captured_messages)

    assert captured_messages == [invalid_line]


async def test_multiple_connect(client, client_protocol):
    """Calling connect while already connected doesn't do anything"""
    assert client.protocol is client_protocol
    await client.connect()
    assert client.protocol is client_protocol


def test_on_signature(client):
    """register a sync handler with full function signature options"""

    def handle(arg, /, pos_only, *args, kw_only, kw_default="d", **kwargs):
        pass

    client.on("f")(handle)
    client.on("f", handle)


def test_on_coroutine(client):
    async def handle(arg, /, pos_only, *args, kw_only, kw_default="d", **kwargs):
        pass

    client.on("f")(handle)
    client.on("f", handle)


async def test_trigger_no_handlers(client):
    """trigger an event with no handlers"""
    task = client.trigger("some event")
    assert not client.event_handlers["SOME EVENT"]
    assert client.triggers["SOME EVENT"] == 1

    await asyncio.sleep(0)
    assert task.done()


async def test_trigger_one_handler(client):
    called = []
    client.on("f")(lambda: called.append(1))
    client.trigger("f")
    assert not called

    await asyncio.sleep(0)
    assert client.triggers["F"] == 1
    assert called == [1]


async def test_trigger_multiple_handlers(client):
    h1, h2 = 0, 0

    def incr(first=True):
        nonlocal h1, h2
        if first:
            h1 += 1
        else:
            h2 += 1

    client.on("f")(lambda: incr(first=True))
    client.on("f")(lambda: incr(first=False))
    client.trigger("f")
    assert h1 == h2 == 0

    await asyncio.sleep(0)
    assert h1 == 1
    assert h2 == 1


async def test_trigger_unpacking(client):
    """Usual semantics for unpacking **kwargs"""
    called = False

    def func(arg, *args, kw_only, kw_default="default", **kwargs):
        assert arg == "arg"
        assert not args
        assert kw_only == "kw_only"
        assert kw_default == "default"
        assert kwargs["extra"] == "extra"
        nonlocal called
        called = True

    client.on("f")(func)
    client.trigger("f", **{s: s for s in ["arg", "kw_only", "extra"]})
    await asyncio.sleep(0)
    assert called


async def test_bound_method_of_instance(client):
    """verify bound methods are correctly inspected"""
    called = False

    class Class(object):
        def method(self, arg, kw_default="default"):
            assert arg == "arg"
            assert kw_default == "default"
            nonlocal called
            called = True

    instance = Class()
    client.on("f")(instance.method)
    client.trigger("f", **{"arg": "arg"})
    await asyncio.sleep(0)
    assert called


async def test_bound_async_method_of_instance(client):
    """verify bound methods are correctly inspected"""
    called = False

    class Class(object):
        async def method(self, arg, kw_default="default"):
            assert arg == "arg"
            assert kw_default == "default"
            nonlocal called
            called = True

    instance = Class()
    client.on("f")(instance.method)
    client.trigger("f", **{"arg": "arg"})
    await asyncio.sleep(0)
    assert called


async def test_callback_ordering(client):
    """Callbacks for a second event don't queue behind the first event"""
    second_complete = asyncio.Event()
    call_order = []
    complete_order = []

    async def first():
        call_order.append("first")
        await second_complete.wait()
        complete_order.append("first")

    async def second():
        call_order.append("second")
        complete_order.append("second")
        second_complete.set()

    client.on("f")(first)
    client.on("f")(second)

    all_handlers = client.trigger("f")
    await all_handlers

    assert call_order == ["first", "second"]
    assert complete_order == ["second", "first"]


async def test_wait_ordering(client):
    """Handlers are enqueued before trigger waits"""
    invoked = []

    @client.on("some.trigger")
    def handle(**kwargs):
        invoked.append("handler")

    async def waiter():
        invoked.append("start waiting")
        await client.wait("some.trigger")
        invoked.append("done waiting")

    wait_task = create_task(waiter())
    await asyncio.sleep(0)  # let waiter get to `await client.wait()`
    trigger_task = client.trigger("some.trigger")
    await join_tasks([wait_task, trigger_task])

    assert invoked == ["start waiting", "handler", "done waiting"]


async def test_wait_return_value(client):
    """The value returned should be the same as the value given."""
    event_name = "my-event"

    record = []

    async def waiter():
        record.append("start waiting")
        record.append(await client.wait(event_name))
        record.append("done waiting")

    record.append("create")
    create_task(waiter())
    record.append("yield1")
    await asyncio.sleep(0)
    record.append("trigger")
    await client.trigger(event_name)
    record.append("yield2")
    await asyncio.sleep(0)

    expected = [
        "create",
        "yield1",
        "start waiting",
        "trigger",
        "yield2",
        event_name,
        "done waiting",
    ]

    assert record == expected
