"""
    Uses simplex for quickly routing messages with basic matching.
    See https://github.com/numberoverzero/simplex for pattern options


    Consider a bot that echoes everything of the following format:

        "Say [words], bot"

    This can be implemented as:

        bot = Client(...)
        router = router.Router(bot)

        @router.route("Say [words], bot")
        def handle(nick, target, fields):
            # Respond direct to private messages
            if target==bot.NICK:
                target = nick
            message = fields["words"]
            router.bot.send("PRIVMSG", target=target, message=message)

"""
import asyncio
import functools
import simplex


class Router(object):
    def __init__(self, client):
        self.client = client
        self.routes = {}
        client.on("PRIVMSG")(self._handle)

    def _handle(self, nick, target, message):
        """ client callback entrance """
        for regex, (func, pattern) in self.routes.items():
            match = regex.match(message)
            if match:
                fields = match.groupdict()
                self.client.loop.create_task(func(nick, target, fields))

    def route(self, pattern, func=None, **kwargs):
        """Register a callback for a given pattern

        @router.route("client, say [words]")
        def handle(nick, target, fields):
            # PRIVMSG - respond in kind
            if target==router.client.NICK:
                target = nick
            message = fields["words"]
            router.client.send("PRIVMSG", target=target, message=message)

        """
        if func is None:
            return functools.partial(self.route, pattern)

        # Decorator should always return the original function
        wrapped = func
        if not asyncio.iscoroutinefunction(wrapped):
            wrapped = asyncio.coroutine(wrapped)

        compiled = simplex.compile(pattern)
        self.routes[compiled] = (wrapped, pattern)
        return func
