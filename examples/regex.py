import asyncio
import re
import typing as t

from bottom import Client
from bottom.util import create_task


class Router(object):
    def __init__(self, client: Client) -> None:
        self.client = client
        self.routes = {}
        client.on("privmsg")(self._handle_privmsg)

    async def _handle_privmsg(self, **kwargs: t.Any) -> None:
        """client callback entrance"""
        for regex, (func, pattern) in self.routes.items():
            match = regex.match(kwargs["message"])
            if match:
                kwargs.update({"match": match, "pattern": pattern})
                create_task(func(**kwargs))

    def route[T: t.Coroutine](self, pattern: str | re.Pattern[str]) -> t.Callable[[T], T] | T:
        def decorator(fn: T) -> T:
            assert asyncio.iscoroutinefunction(fn), f"{fn} must be async to register"
            if isinstance(pattern, str):
                compiled = re.compile(pattern)
            else:
                compiled = pattern
            self.routes[compiled] = (fn, compiled.pattern)
            return fn

        return decorator


if __name__ == "__main__":
    # Common client setup for all examples
    from examples.common import NICK, client, run

    router = Router(client)

    @router.route(r"^bot, say (\w+) please$")
    async def echo(nick: str, target: str, match: re.Match, **kwargs: t.Any) -> None:
        # Don't echo ourselves
        if nick == NICK:
            return
        # Respond directly to direct messages
        if target == NICK:
            target = nick
        await client.send("privmsg", target=target, message=match.group(1))

    run()
