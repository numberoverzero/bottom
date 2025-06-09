from __future__ import annotations

import asyncio
import logging
import ssl
import typing as t

from bottom.core import BaseClient, ClientMessageHandler, NextMessageHandler
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
        :param host: The IRC server address to connect to.
        :param port: The port of the IRC server.
        :param encoding: The character encoding to use.  Default is utf-8.
        :param ssl:
            Whether SSL should be used while connecting.
            Default is True.
        """
        super().__init__(host, port, encoding=encoding, ssl=ssl)
        self.message_handlers.append(rfc2812_handler(self))

    def send(self, command: str, **kwargs: t.Any) -> None:
        """
        Send a message to the server.

        .. code-block:: python

            client.send("nick", nick="weatherbot")
            client.send("privmsg", target="#python", message="Hello, World!")

        """
        packed_command = pack_command(command, **kwargs).strip()
        self.send_message(packed_command)


rfc2812_log = logging.getLogger("bottom.rfc2812_handler")


def rfc2812_handler(client: Client) -> ClientMessageHandler:
    async def handler(next_handler: NextMessageHandler, message: str) -> None:
        try:
            event, kwargs = unpack_command(message)
            client.trigger(event, **kwargs)
        except ValueError:
            rfc2812_log.debug("Failed to parse line >>> {}".format(message))
        await next_handler(message)

    return handler


async def wait_for(client: Client, events: list[str], *, mode: t.Literal["first", "all"] = "first") -> list[str]:
    """
    Wait for one or all of the events to happen, depending on mode.

    ```
    wait_for = make_waiter(client)

    # race for first event
    completed = await wait_for("RPL_ENDOFMOTD", "ERR_NOMOTD", mode="first")
    print(f"first done: {completed}")

    # wait for all events
    completed = await wait_for(
        "RPL_MOTDSTART",
        "RPL_MOTD",
        "RPL_ENDOFMOTD",
        mode="all"
    )
    print("collected whole MOTD")
    ```
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
    for future in pending:
        future.cancel()
    return ret
