import asyncio
import typing as t

from bottom import Client
from bottom.client import wait_for

host = "irc.libera.chat"
port = 6697
ssl = True

NICK = "bottom-bot"
CHANNEL = "#bottom-dev"

client = Client(host=host, port=port, ssl=ssl)


@client.on("ping")
async def handle(message: str, **kwargs: t.Any) -> None:
    await client.send("pong", message=message)


@client.on("client_connect")
async def on_connect(**kwargs: t.Any) -> None:
    await client.send("nick", nick=NICK)
    await client.send("user", user=NICK, realname="https://github.com/numberoverzero/bottom")

    # This waits for the 'rpl_endofmotd' and 'err_nomotd' commands,
    # returning when one of them is triggered. 'events' is a list,
    # but it will only contain one item in this case since only one
    # of these commands will be sent by the server.
    events = await wait_for(client, ["rpl_endofmotd", "err_nomotd"], mode="first")

    # The event names returned are the same as the ones given, so
    # we can easily check for them in the result.
    if "rpl_endofmotd" in events:
        print("MOTD returned")
    elif "err_nomotd" in events:
        print("No MOTD returned")

    await client.send("join", channel=CHANNEL)


async def async_run(run_client: Client = client) -> None:
    print(f"connecting to {host}:{port} as {NICK} in {CHANNEL}")
    await run_client.connect()
    try:
        await run_client.wait("client_disconnect")
        print("\ndisconnected by remote")
    except asyncio.CancelledError:
        await run_client.disconnect()
        print("\ndisconnected after ctrl+c")


def run(run_client: Client = client) -> None:
    asyncio.run(async_run(run_client))
