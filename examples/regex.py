import re
import typing as t

from bottom.core import BaseClient
from bottom.util import Decorator, create_task, ensure_async_fn


class Router(object):
    def __init__(self, client: BaseClient) -> None:
        self.client = client
        self.routes = {}
        client.on("privmsg")(self._route_privmsg)

    async def _route_privmsg(self, nick: str, target: str, message: str, **kwargs: t.Any) -> None:
        """client callback entrance"""
        for regex, (func, pattern) in self.routes.items():
            match = regex.match(message)
            if match:
                create_task(func(nick, target, message, match, **kwargs))

    @t.overload
    def route[**P, R](self, pattern: str | re.Pattern, fn: None = None) -> Decorator[P, R]: ...
    @t.overload
    def route[**P, R](self, pattern: str | re.Pattern, fn: t.Callable[P, R]) -> t.Callable[P, R]: ...

    def route[**P, R](
        self, pattern: str | re.Pattern, fn: t.Callable[P, R] | None = None
    ) -> Decorator[P, R] | t.Callable[P, R]:
        def decorator(fn: t.Callable[P, R]) -> t.Callable[P, R]:
            async_fn = ensure_async_fn(fn)
            if isinstance(pattern, str):
                compiled = re.compile(pattern)
            else:
                compiled = pattern
            self.routes[compiled] = (async_fn, pattern)
            return fn

        return decorator if fn is None else decorator(fn)


if __name__ == "__main__":
    # Common client setup for all examples
    from examples.common import NICK, client, run

    router = Router(client)

    @router.route(r"^bot, say (\w+)\.$")
    def echo(nick: str, target: str, message: str, match: re.Match, **kwargs: t.Any) -> None:
        # Don't echo ourselves
        if nick == NICK:
            return
        # Respond directly to direct messages
        if target == NICK:
            target = nick
        client.send("privmsg", target=target, message=match.group(1))

    run()
