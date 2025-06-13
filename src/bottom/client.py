from __future__ import annotations

import asyncio
import logging
import ssl
import typing as t

from bottom.core import BaseClient, NextMessageHandler
from bottom.pack import pack_command
from bottom.unpack import unpack_command
from bottom.util import create_task

__all__ = ["Client", "rfc2812_handler", "wait_for"]


class Client(BaseClient):
    def __init__(
        self,
        host: str,
        port: int,
        *,
        encoding: str = "utf-8",
        ssl: bool | ssl.SSLContext = True,
    ) -> None:
        """
        Create a new client that can interact with an IRC server.

        The client does not automatically connect.  Instead, use
        :meth:`connect <bottom.Client.connect>`

        Args:
            host: the server's host
            port: the server's port
            encoding: the encoding to use when converting from bytes
                over the wire.  This is almost always "utf-8"
            ssl: ``True`` to create an ssl context, ``False`` to not use ssl,
                or provide your own ssl context.
        """
        super().__init__(host, port, encoding=encoding, ssl=ssl)
        self.message_handlers.append(rfc2812_handler)

    @t.overload
    async def send(self, command: t.Literal["pass"], *, password: str, **kwargs: t.Any) -> None: ...
    @t.overload
    async def send(self, command: t.Literal["nick"], *, nick: str, **kwargs: t.Any) -> None: ...
    @t.overload
    async def send(
        self, command: t.Literal["user"], *, user: str, mode: int = 0, realname: str, **kwargs: t.Any
    ) -> None: ...
    @t.overload
    async def send(self, command: t.Literal["oper"], *, user: str, password: str, **kwargs: t.Any) -> None: ...
    @t.overload
    async def send(
        self, command: t.Literal["usermode"], *, nick: str | None = None, modes: str | None = None, **kwargs: t.Any
    ) -> None: ...
    @t.overload
    async def send(
        self, command: t.Literal["service"], *, nick: str, distribution: str, type: str, info: str, **kwargs: t.Any
    ) -> None: ...
    @t.overload
    async def send(self, command: t.Literal["quit"], *, message: str | None = None, **kwargs: t.Any) -> None: ...
    @t.overload
    async def send(
        self, command: t.Literal["squit"], *, server: str, message: str | None = None, **kwargs: t.Any
    ) -> None: ...
    @t.overload
    async def send(
        self,
        command: t.Literal["join"],
        *,
        channel: str | t.Iterable[str],
        key: str | t.Iterable[str] | None = None,
        **kwargs: t.Any,
    ) -> None: ...
    @t.overload
    async def send(
        self, command: t.Literal["part"], *, channel: str | t.Iterable[str], message: str | None = None, **kwargs: t.Any
    ) -> None: ...
    @t.overload
    async def send(
        self,
        command: t.Literal["channelmode"],
        *,
        channel: str,
        params: str | t.Iterable[str] | None = None,
        **kwargs: t.Any,
    ) -> None: ...
    @t.overload
    async def send(
        self, command: t.Literal["topic"], *, channel: str, message: str | None = None, **kwargs: t.Any
    ) -> None: ...
    @t.overload
    async def send(
        self,
        command: t.Literal["names"],
        *,
        channel: str | t.Iterable[str] | None = None,
        target: str | None = None,
        **kwargs: t.Any,
    ) -> None: ...
    @t.overload
    async def send(
        self,
        command: t.Literal["list"],
        *,
        channel: str | t.Iterable[str] | None = None,
        target: str | None = None,
        **kwargs: t.Any,
    ) -> None: ...
    @t.overload
    async def send(self, command: t.Literal["invite"], *, nick: str, channel: str, **kwargs: t.Any) -> None: ...
    @t.overload
    async def send(
        self,
        command: t.Literal["kick"],
        *,
        nick: str | t.Iterable[str],
        channel: str | t.Iterable[str],
        message: str | None = None,
        **kwargs: t.Any,
    ) -> None: ...
    @t.overload
    async def send(self, command: t.Literal["privmsg"], *, target: str, message: str, **kwargs: t.Any) -> None: ...
    @t.overload
    async def send(self, command: t.Literal["notice"], *, target: str, message: str, **kwargs: t.Any) -> None: ...
    @t.overload
    async def send(self, command: t.Literal["motd"], *, target: str | None = None, **kwargs: t.Any) -> None: ...
    @t.overload
    async def send(
        self, command: t.Literal["lusers"], *, mask: str | None = None, target: str | None = None, **kwargs: t.Any
    ) -> None: ...
    @t.overload
    async def send(self, command: t.Literal["version"], *, target: str | None = None, **kwargs: t.Any) -> None: ...
    @t.overload
    async def send(
        self, command: t.Literal["stats"], *, query: str | None = None, target: str | None = None, **kwargs: t.Any
    ) -> None: ...
    @t.overload
    async def send(
        self, command: t.Literal["links"], *, mask: str | None = None, remote: str | None = None, **kwargs: t.Any
    ) -> None: ...
    @t.overload
    async def send(self, command: t.Literal["time"], *, target: str | None = None, **kwargs: t.Any) -> None: ...
    @t.overload
    async def send(
        self, command: t.Literal["connect"], *, target: str, port: int, remote: str | None = None, **kwargs: t.Any
    ) -> None: ...
    @t.overload
    async def send(self, command: t.Literal["trace"], *, target: str | None = None, **kwargs: t.Any) -> None: ...
    @t.overload
    async def send(self, command: t.Literal["admin"], *, target: str | None = None, **kwargs: t.Any) -> None: ...
    @t.overload
    async def send(self, command: t.Literal["info"], *, target: str | None = None, **kwargs: t.Any) -> None: ...
    @t.overload
    async def send(
        self, command: t.Literal["servlist"], *, mask: str | None = None, type: str | None = None, **kwargs: t.Any
    ) -> None: ...
    @t.overload
    async def send(self, command: t.Literal["squery"], *, target: str, message: str, **kwargs: t.Any) -> None: ...
    @t.overload
    async def send(
        self, command: t.Literal["who"], *, mask: str | None = None, o: bool | None = None, **kwargs: t.Any
    ) -> None: ...
    @t.overload
    async def send(
        self, command: t.Literal["whois"], *, mask: str | t.Iterable[str], target: str | None = None, **kwargs: t.Any
    ) -> None: ...
    @t.overload
    async def send(
        self,
        command: t.Literal["whowas"],
        *,
        nick: str | t.Iterable[str],
        count: int | None = None,
        target: str | None = None,
        **kwargs: t.Any,
    ) -> None: ...
    @t.overload
    async def send(self, command: t.Literal["kill"], *, nick: str, message: str, **kwargs: t.Any) -> None: ...
    @t.overload
    async def send(
        self, command: t.Literal["ping"], *, message: str, target: str | None = None, **kwargs: t.Any
    ) -> None: ...
    @t.overload
    async def send(self, command: t.Literal["pong"], *, message: str | None = None, **kwargs: t.Any) -> None: ...
    @t.overload
    async def send(self, command: t.Literal["away"], *, message: str | None = None, **kwargs: t.Any) -> None: ...
    @t.overload
    async def send(self, command: t.Literal["rehash"], **kwargs: t.Any) -> None: ...
    @t.overload
    async def send(self, command: t.Literal["die"], **kwargs: t.Any) -> None: ...
    @t.overload
    async def send(self, command: t.Literal["restart"], **kwargs: t.Any) -> None: ...
    @t.overload
    async def send(
        self,
        command: t.Literal["summon"],
        *,
        nick: str,
        target: str | None = None,
        channel: str | None = None,
        **kwargs: t.Any,
    ) -> None: ...
    @t.overload
    async def send(self, command: t.Literal["users"], *, target: str | None = None, **kwargs: t.Any) -> None: ...
    @t.overload
    async def send(self, command: t.Literal["wallops"], *, message: str | None = None, **kwargs: t.Any) -> None: ...
    @t.overload
    async def send(self, command: t.Literal["userhost"], *, nick: str | t.Iterable[str], **kwargs: t.Any) -> None: ...
    @t.overload
    async def send(self, command: t.Literal["ison"], *, nick: str | t.Iterable[str], **kwargs: t.Any) -> None: ...
    @t.overload
    async def send(self, command: str, **kwargs: t.Any) -> None: ...
    async def send(self, command: str, **kwargs: t.Any) -> None:
        """
        Send a message to the server.

        ::

            await client.send("privmsg", target="n/0", message="it works!")
            await client.send("privmsg", target="#mychan", message="hello, world")

            await client.send("join", target="#mychan")
            await client.send("part", target="#mychan")

        See :ref:`Commands<Commands>` for the list of supported rfc2812 commands.

        """
        packed_command = pack_command(command, **kwargs).strip()
        await self.send_message(packed_command)


rfc2812_log = logging.getLogger("bottom.rfc2812_handler")


async def rfc2812_handler(next_handler: NextMessageHandler[Client], client: Client, message: bytes) -> None:
    try:
        event, kwargs = unpack_command(message.decode(client._encoding))
        client.trigger(event, **kwargs)
    except ValueError:
        rfc2812_log.debug("Failed to parse line >>> {}".format(message.decode(client._encoding)))
    await next_handler(client, message)


async def wait_for(client: Client, events: list[str], *, mode: t.Literal["first", "all"] = "first") -> list[dict]:
    """
    Wait for one or all of the events to happen, depending on mode.

    The results are the dicts that each event was triggered with, and the event name stored in the key ``"__event__"``

    When waiting for the first event, note that more than one may trigger::

        from bottom import wait_for

        async def on_first():
            completed = await wait_for(
                client,
                ["RPL_ENDOFMOTD", "ERR_NOMOTD"],
                mode="first"
            )
            names = [o["__event__"] for o in completed]
            print(f"first task(s) done: {names}")

    When waiting for all, the return order is the same as the input order, not necessarily the
    completion order::

        async def all_events():
            completed = await wait_for(
                client,
                ["RPL_MOTDSTART", "RPL_MOTD", "RPL_ENDOFMOTD"],
                mode="all"
            )
            print("collected whole MOTD")
            names = [o["__event__"] for o in completed]
            assert names == ["RPL_MOTDSTART", "RPL_MOTD", "RPL_ENDOFMOTD"]
    """
    if not events:
        return []
    tasks = [create_task(client.wait(event)) for event in events]
    return_when = {
        "first": asyncio.FIRST_COMPLETED,
        "all": asyncio.ALL_COMPLETED,
    }[mode]
    done, pending = await asyncio.wait(tasks, return_when=return_when)

    ret = [future.result() for future in done]
    if mode == "all":
        assert not pending
    for future in pending:
        future.cancel()
    return ret
