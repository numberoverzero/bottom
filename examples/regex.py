import asyncio
import functools
import re


class Router(object):
    def __init__(self, client):
        self.client = client
        self.routes = {}
        client.on("privmsg")(self._handle)

    def _handle(self, nick, target, message, **kwargs):
        """ client callback entrance """
        for regex, (func, pattern) in self.routes.items():
            match = regex.match(message)
            if match:
                asyncio.create_task(
                    func(nick, target, message, match, **kwargs))

    def route(self, pattern, func=None, **kwargs):
        if func is None:
            return functools.partial(self.route, pattern)

        # Decorator should always return the original function
        wrapped = func
        if not asyncio.iscoroutinefunction(wrapped):
            wrapped = asyncio.coroutine(wrapped)

        compiled = re.compile(pattern)
        self.routes[compiled] = (wrapped, pattern)
        return func


if __name__ == "__main__":
    # Common client setup for all examples
    from common import NICK, client, run
    router = Router(client)


    @router.route("^bot, say (\w+)\.$")
    def echo(nick, target, message, match, **kwargs):
        # Don't echo ourselves
        if nick == NICK:
            return
        # Respond directly to direct messages
        if target == NICK:
            target = nick
        client.send("privmsg", target=target, message=match.group(1))

    run()
