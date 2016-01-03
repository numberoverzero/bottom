import asyncio
from typing import Callable

from . import connection
from . import event
from . import pack
from . import unpack

__all__ = ["Client"]
__version__ = "1.0.0"


class Client(event.EventsMixin):
    __conn_cls = connection.Connection

    def __init__(self, host: str, port: str, *, encoding: str = 'UTF-8',
                 ssl: bool = True, loop: asyncio.BaseEventLoop = None) -> None:
        """
        :param host: The IRC server address to connect to.
        :param port: The port of the IRC server.
        :param encoding: The character encoding to use.
        :param ssl: Whether SSL should be used while connecting.
        :param loop: The event loop to use. Omit unless you know what you're
        doing.
        """
        if loop is None:
            loop = asyncio.get_event_loop()
        super().__init__(unpack.parameters, loop=loop)
        self.connection = self.__conn_cls(host, port, self, ssl=ssl,
                                          encoding=encoding, loop=loop)

    def send(self, command: str, **kwargs) -> None:
        """
        Send a message to the server.

        Examples:

        .. code-block:: python

            client.send('nick', nick='weatherbot')
            client.send('privmsg', target='#python', message="Hello, World!")

        """
        packed_command = pack.pack_command(command, **kwargs)
        self.connection.send(packed_command)

    async def connect(self) -> None:
        """
        Triggers a connection to the defined server.
        """
        await self.connection.connect()

    async def disconnect(self) -> None:
        """
        Triggers a disconnect to the defined server.
        """
        await self.connection.disconnect()

    @property
    def connected(self) -> bool:
        """
        :return: Whether the bot is connected or not.
        """
        return self.connection.connected

    async def run(self) -> None:
        """
        Run the client until it disconnects (without reconnecting)
        """
        await self.connection.run()

    def on(self, command: str) -> Callable:
        """
        Decorate a function to be invoked when a :param:`command` occurs.

        :param command: The name of the command.
        """
        return super().on(command.upper())
