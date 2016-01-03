"""
    Uses simplex for quickly routing messages with basic matching.
    See https://github.com/numberoverzero/simplex for pattern options


    Consider a bot that echoes everything of the following format:

        "Say [words], bot"

    This can be implemented as:

    .. code-block:: python

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
import asyncio
from typing import Callable

import simplex

from bottom import Client


class Router(object):
    def __init__(self, bot: Client) -> None:
        """
        :type bot: A client object.
        """
        self.bot = bot
        self.routes = {}
        bot.on("PRIVMSG")(self.handle)

    def handle(self, nick: str, target: str, message: str) -> None:
        """
        Bot callback entrance.
        :param nick: The nickname of the sending user.
        :param target: The target of the message.
        :param message: The message contents.
        """
        for regex, (func, pattern) in self.routes.items():
            match = regex.match(message)
            if match:
                fields = match.groupdict()
                self.bot.loop.create_task(func(nick, target, fields))

    def route(self, pattern: str, **kwargs) -> Callable:
        """
        Decorator for wiring up functions

        Example:

        .. code-block:: python

            @router.route("bot, say [words]", ignore_case=True)
            def handle(nick, target, fields):
                # PRIVMSG - respond in kind
                if target==router.bot.NICK:
                    target = nick
                router.bot.send("PRIVMSG", target=target, message=fields['words'])

        :param pattern: A regex pattern to match.
        """

        def wrapper(function: Callable) -> Callable:
            wrapped = function
            if not asyncio.iscoroutinefunction(wrapped):
                wrapped = asyncio.coroutine(wrapped)
            compiled = simplex.compile(pattern)
            self.routes[compiled] = (wrapped, pattern)
            return function

        return wrapper
