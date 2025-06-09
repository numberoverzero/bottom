import asyncio

from bottom.core import Protocol

from tests.conftest import busy_wait


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
