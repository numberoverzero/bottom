import collections
import asyncio
import logging
from . import rfc

logger = logging.getLogger(__name__)

LOCAL_COMMANDS = set(
    "CLIENT_CONNECT",
    "CLIENT_DISCONNECT"
)


def get_command(command):
    '''
    Augment command lookup to include special client-side events

    This allows us to hook into events like CLIENT_CONNECT,
    which are not part of the IRC spec.

    '''
    command = command.upper()
    if command in LOCAL_COMMANDS:
        return command
    return rfc.unique_command(command)


class Client(object):
    def __init__(self, host, port):
        self.handler = Handler()
        self.connection = Connection(host, port, self.handlers)

    def run(self):
        ''' Run the bot forever '''
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.connection.loop())

    def on(self, command):
        '''
        Decorate a function to be invoked on any :param:`command` message.

        Returns
        -------
        A function decorator that adds the decorated function to this
        :class:`~Client` handlers and returns the underlying function.

        Example
        -------

        bot = Client('localhost', 6697)

        @bot.on('client_connect')
        def autojoin(host, port):
            bot.send('NICK', 'weatherbot')
            bot.send('USER', 'weatherbot', 0,
                     '*', message="Bill's Weather Bot")
            bot.send('JOIN', '#weather-alert')
            bot.send('JOIN', '#weather-interest')

        bot.run()
        '''
        command = get_command(command)

        def wrap(func):
            ''' Add the function to this client's handlers and return it '''
            self.handler.add(command, func)
            return func
        return wrap

    def send(self, command, *params, message=None, prefix=None):
        '''
        Send a message to the server.

        :param:`prefix` and :param:`message` will be prefixed with a ':'

        Examples
        --------
        bot.send('nick', 'weatherbot')
        bot.send('user', 'weatherbot', 0, '*', message='Real Name')

        '''
        self.connection.send(rfc.wire_format(
            command,
            params=params,
            message=message,
            prefix=prefix
        ))


class Connection(object):
    def __init__(self, host, port, handler):
        self.host, self.port = host, port
        self.reader, self.writer = None, None

        self.handle = handler
        self.encoding = 'UTF-8'
        self.ssl = True

    @asyncio.coroutine
    def connect(self):
        self.reader, self.writer = yield from asyncio.open_connection(
            self.host, self.port, ssl=self.ssl)
        yield from self.handle("CLIENT_CONNECT", self.host, self.port)

    @asyncio.coroutine
    def disconnect(self):
        if self.reader:
            self.reader.close()
            self.reader = None
        if self.writer:
            self.writer.close()
            self.writer = None
        yield from self.handle("CLIENT_DISCONNECT", self.host, self.port)

    @asyncio.coroutine
    def reconnect(self):
        yield from self.disconnect()
        yield from self.connect()

    @asyncio.coroutine
    def loop(self):
        self.connect()
        while True:
            msg = yield from self.read()
            if msg:
                # Don't propegate the message if parser doesn't understand it
                args = rfc.parse(msg)
                if args:
                    yield from self.handle(*args)
            else:
                # Lost connection
                yield from self.reconnect()

    def send(self, msg):
        self.writer.write((msg.strip() + '\n').encode(self.encoding))

    @asyncio.coroutine
    def read(self):
        try:
            msg = yield from self.read.readline()
            return msg.decode(self.encoding, 'ignore').strip()
        except EOFError:
            return ''


class Handler(object):
    def __init__(self):
        self.coros = collections.defaultdict(set)

    def add(self, command, func):
        # Wrap the function in a coroutine so that we can
        # create a task list and use asyncio.wait
        command = get_command(command)
        coro = asyncio.coroutine(func)
        self.coros[command].add(coro)

    @asyncio.coroutine
    def __call__(self, command, *args, **kwargs):
        logger.debug('HANDLE <{}> ARGS <{}> KWARGS <{}>'.format(
            command, args, kwargs))
        coros = self.coros[get_command(command)]
        tasks = [coro(*args, **kwargs) for coro in coros]
        asyncio.wait(tasks)
