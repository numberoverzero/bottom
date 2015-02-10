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

            message = fields['words']
            router.bot.send("PRIVMSG", target=target, message=message)

"""
import simplex


class Router(object):
    def __init__(self, bot):
        self.bot = bot
        self.routes = {}
        bot.on("PRIVMSG")(self.handle)

    def handle(self, nick, target, message):
        ''' bot callback entrance '''
        for regex, (func, pattern) in self.routes.items():
            match = regex.match(message)
            if match:
                fields = match.groupdict()
                func(nick, target, fields)
                break

    def route(self, pattern, **kwargs):
        '''
        decorator for wiring up functions

        @router.route("bot, say [words]", ignore_case=True)
        def handle(nick, target, fields):
            # PRIVMSG - respond in kind
            if target==router.bot.NICK:
                target = nick
            router.bot.send("PRIVMSG", target=target, message=fields['words'])

        '''
        def wrapper(function):
            compiled = simplex.compile(pattern)
            self.routes[compiled] = (function, pattern)
            return function
        return wrapper
