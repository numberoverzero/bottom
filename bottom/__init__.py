""" asyncio-based rfc2812-compliant IRC Client """
import logging
import asyncio
from . import connection
from . import event
from . import pack
from . import unpack
__all__ = ["Client"]
logger = logging.getLogger(__name__)


class Client(event.EventsMixin):
    __conn_cls__ = connection.Connection

    def __init__(self, host, port, encoding='UTF-8', ssl=True):
        # It's ok that unpack.parameters isn't cached, since it's only
        # called when adding an event handler (which should __usually__
        # only occur during setup)
        super().__init__(unpack.parameters)
        # trigger events on the client
        self.connection = self.__conn_cls__(host, port, self,
                                            encoding=encoding, ssl=ssl)

    def send(self, command, **kwargs):
        '''
        Send a message to the server.

        Examples
        --------
        client.send('nick', nick='weatherbot')
        client.send('privmsg', target='#python', message="Hello, World!")

        '''
        packed_command = pack.pack_command(command, **kwargs)
        self.connection.send(packed_command)

    @asyncio.coroutine
    def connect(self):
        yield from self.connection.connect()

    @asyncio.coroutine
    def disconnect(self):
        yield from self.connection.disconnect()

    @property
    def connected(self):
        return self.connection.connected

    @asyncio.coroutine
    def run(self, loop=None):
        ''' Run the client until it disconnects (without reconnecting) '''
        yield from self.connection.run(loop=loop)

    def on(self, command):
        '''
        Decorate a function to be invoked when a :param:`command` occurs.
        '''
        return super().on(command.upper())
