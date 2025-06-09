import asyncio
import signal
import typing as t

from bottom import Client
from bottom.client import wait_for
from bottom.util import create_task

host = "chat.freenode.net"
port = 6697
ssl = True

NICK = "bottom-bot"
CHANNEL = "#bottom-dev"

client = Client(host=host, port=port, ssl=ssl)


# taken from :ref:`Patterns`
@client.on("ping")
def handle(message: str, **kwargs: t.Any) -> None:
    client.send("pong", message=message)


@client.on("client_connect")
async def on_connect(**kwargs: t.Any) -> None:
    client.send("nick", nick=NICK)
    client.send("user", user=NICK, realname="https://github.com/numberoverzero/bottom")

    # This waits for the 'rpl_endofmotd' and 'err_nomotd' commands,
    # returning when one of them is triggered. 'events' is a list,
    # but it will only contain one item in this case since only one
    # of these commands will be sent by the server.
    events = await wait_for(client, ["rpl_endofmotd", "err_nomotd"], mode="first")
    print("Connection made")

    # The event names returned are the same as the ones given, so
    # we can easily check for them in the result.
    if "rpl_endofmotd" in events:
        print("MOTD returned")
    elif "err_nomotd" in events:
        print("No MOTD returned")

    client.send("join", channel=CHANNEL)


def run() -> None:
    async def async_run() -> None:
        print(f"connecting to {host}:{port} as {NICK} in {CHANNEL}")
        await client.connect()
        await client.wait("client_disconnect")
        print("shutting down")

    def ctrl_c() -> None:
        create_task(client.disconnect())

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, ctrl_c)
    loop.run_until_complete(async_run())
