import collections
import asyncio
import inspect
import route
import rfc
missing = object()  # sentinel
LOCAL_COMMANDS = set([
    "CLIENT_CONNECT",
    "CLIENT_DISCONNECT"
])


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
        self.connection = Connection(host, port, self.handler)

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
        yield from self.handle("CLIENT_CONNECT",
                               {'host': self.host, 'port': self.port})

    @asyncio.coroutine
    def disconnect(self):
        if self.reader:
            self.reader = None
        if self.writer:
            self.writer.close()
            self.writer = None
        yield from self.handle("CLIENT_DISCONNECT",
                               {'host': self.host, 'port': self.port})

    @asyncio.coroutine
    def reconnect(self):
        yield from self.disconnect()
        yield from self.connect()

    @asyncio.coroutine
    def loop(self):
        yield from self.connect()
        while True:
            msg = yield from self.read()
            if msg:
                # (prefix, command, params, message)
                args = rfc.parse(msg)
                # Don't propegate the message if parser doesn't understand it
                if not args:
                    continue
                # Unpack args -> python dict
                command, kwargs = route.unpack(*args)
                # Handler will map kwargs to each func's expected args
                yield from self.handle(command, kwargs)
            else:
                # Lost connection
                yield from self.reconnect()

    def send(self, msg):
        msg = msg.strip()
        self.writer.write((msg + '\n').encode(self.encoding))

    @asyncio.coroutine
    def read(self):
        try:
            msg = yield from self.reader.readline()
            return msg.decode(self.encoding, 'ignore').strip()
        except EOFError:
            return ''


class Handler(object):
    def __init__(self):
        # Dictionary of command : set(func)
        # where command is a valid local or rfc command, and set(func) is the
        # set of functions that will be invoked when the given command is
        # called on the Handler.
        self.coros = collections.defaultdict(set)

    def add(self, command, func):
        # Wrap the function in a coroutine so that we can
        # create a task list and use asyncio.wait
        command = get_command(command)
        # Fail fast if the function's signature doesn't match the possible
        # fields for this command.
        route.validate(command, func)
        # Pre-compute as much of the binding process as possible.
        # Then, invoking the function with appropriate arguments should be
        # a simple dict copy/update and call(signature.bind)
        partial = PartialBind(command, func)
        # Wrap the partial as a coroutine so that we can asyncio.wait
        coro = asyncio.coroutine(partial)
        self.coros[command].add(coro)

    @asyncio.coroutine
    def __call__(self, command, kwargs):
        coros = self.coros[get_command(command)]
        if not coros:
            return
        tasks = [coro(kwargs) for coro in coros]
        yield from asyncio.wait(tasks)


class PartialBind(object):
    ''' Custom partial binding for functions that map to commands '''
    def __init__(self, command, func):
        self.sig = inspect.signature(func)
        self.command = command
        self.func = func

        self.load_defaults()

    def load_defaults(self):
        '''
        Only set defaults for keys the function expects

        Functions may not expect all available parameters for the command, so
        we only build a mapping for the ones we care about.

        '''
        self.default = {}
        for key, param in self.sig.parameters.items():
            default = param.default
            #  Has no default - use equivalent of empty
            if default is inspect.Parameter.empty:
                self.default[key] = None
            else:
                self.default[key] = default

    def __call__(self, kwargs):
        unbound = self.default.copy()
        # Only map params this function expects
        for key in unbound:
            new_value = kwargs.get(key, missing)
            # Don't overwrite defaults with nothing
            if new_value not in [missing, None]:
                unbound[key] = new_value
        bound = self.sig.bind(**unbound)
        self.func(*bound.args, **bound.kwargs)
