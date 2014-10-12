""" asyncio-based rfc2812-compliant IRC Client """
import collections
import asyncio
import inspect
import route
import rfc
missing = object()  # sentinel


__all__ = ["Client"]


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
        command = rfc.unique_command(command)

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

    @asyncio.coroutine
    def connect(self):
        yield from self.connection.connect()

    @asyncio.coroutine
    def disconnect(self):
        yield from self.connection.disconnect()


class Connection(object):
    def __init__(self, host, port, handler):
        self.host, self.port = host, port
        self.reader, self.writer = None, None

        self.handle = handler
        self.encoding = 'UTF-8'
        self.ssl = True
        self._connected = False

    @asyncio.coroutine
    def connect(self):
        self.reader, self.writer = yield from asyncio.open_connection(
            self.host, self.port, ssl=self.ssl)
        self._connected = True
        yield from self.handle("CLIENT_CONNECT",
                               {'host': self.host, 'port': self.port})

    @asyncio.coroutine
    def disconnect(self):
        if self.reader:
            self.reader = None
        if self.writer:
            self.writer.close()
            self.writer = None
        self._connected = False
        yield from self.handle("CLIENT_DISCONNECT",
                               {'host': self.host, 'port': self.port})

    @property
    def connected(self):
        return self._connected

    @asyncio.coroutine
    def loop(self):
        yield from self.connect()
        while self.connected:
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
                yield from self.disconnect()
                # Don't fire disconnect event twice
                continue
            # Give the connection a chance to clean up or reconnect
            if not self.connected:
                yield from self.disconnect()

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
        # where command is a string, and set(func) is the set of functions
        # (wrapped and decorated) that will be invoked when the given command
        # is called on the Handler.
        self.partials = collections.defaultdict(set)

    def add(self, command, func):
        '''
        Validate the func's signature, then wrap it in a :class:`~PartialBind`
        to speed up argument injection.
        '''
        command = rfc.unique_command(command)
        route.validate(command, func)
        partial = PartialBind(func)
        self.partials[command].add(partial)

    @asyncio.coroutine
    def __call__(self, command, kwargs):
        ''' This is a coroutine so that we can `yield from` it's execution '''
        partials = self.partials[rfc.unique_command(command)]
        if not partials:
            return
        tasks = [partial(kwargs) for partial in partials]
        yield from asyncio.wait(tasks)


class PartialBind(object):
    ''' Custom partial binding for functions that map to commands '''
    def __init__(self, func):
        # Wrap non-coroutines so we can always `yield from func(*a, **kw)`
        if not asyncio.iscoroutinefunction(func):
            func = asyncio.coroutine(func)
        self.func = func

        self.sig = inspect.signature(func)
        self.default = {}
        for key, param in self.sig.parameters.items():
            default = param.default
            #  Has no default - use equivalent of empty
            if default is inspect.Parameter.empty:
                self.default[key] = None
            else:
                self.default[key] = default

    @asyncio.coroutine
    def __call__(self, kwargs):
        unbound = self.default.copy()
        # Only map params this function expects
        for key in unbound:
            new_value = kwargs.get(key, missing)
            # Don't overwrite defaults with nothing
            if new_value not in [missing, None]:
                unbound[key] = new_value
        bound = self.sig.bind(**unbound)
        yield from self.func(*bound.args, **bound.kwargs)
