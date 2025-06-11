import asyncio
import typing as t

from bottom import Client

type HandlerTakesClient[**P] = t.Callable[t.Concatenate[Client, P], t.Coroutine]


class Registry:
    plugins: dict[str, t.Callable[[Client], None]]

    def __init__(self) -> None:
        self.plugins = {}

    def register[**P](self, event: str, fn: HandlerTakesClient, name: str | None = None) -> None:
        assert asyncio.iscoroutinefunction(fn), f"{fn} must be async to register"

        def apply(client: Client) -> None:
            async def handle(*a: P.args, **kw: P.kwargs) -> None:
                await fn(client, *a, **kw)

            client.on(event)(handle)

        if isinstance(name, str):
            name = name.strip().upper()
        name = name or fn.__name__  # ty: ignore  # https://github.com/astral-sh/ty/issues/599
        if name in self.plugins:
            raise RuntimeError(f"tried to register {fn} as {name!r} but that name is taken.")

        self.plugins[name] = apply

    def enable(self, client: Client, *plugin_names: str) -> None:
        for event in plugin_names:
            apply = self.plugins[event.strip().upper()]
            apply(client)


GLOBAL_REGISTRY = Registry()


def register[T: HandlerTakesClient](
    event: str, *, registry: Registry = GLOBAL_REGISTRY, name: str | None = None
) -> t.Callable[[T], T]:
    def register_plugin(fn: T) -> T:
        registry.register(event, fn, name)
        return fn

    return register_plugin


def enable(client: Client, *plugin_names: str, registry: Registry = GLOBAL_REGISTRY) -> None:
    registry.enable(client, *plugin_names)


if __name__ == "__main__":
    # Common client setup for all examples
    from examples.common import client, run

    @register("ping", name="my.plugins.ping")
    async def handle_ping(client: Client, message: str, **kw: t.Any) -> None:
        print(f"<<< ping {message!r}")
        await client.send("pong", message=message)
        print(f">>> pong {message!r}")

    print("enabling handle_ping plugin")
    enable(client, "my.plugins.ping")
    run()
