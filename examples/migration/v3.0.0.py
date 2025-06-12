# fmt: off
# isort: skip_file
import asyncio
import random
import typing as t

from bottom import Client, NextMessageHandler
# note: this is trivially implemented in your own code, feel free to copy from github or the migration guide
from bottom.util import create_task

HOST = "chat.freenode.net"
PORT = 6697
SSL = True

NICK = "bottom-bot"
CHANNEL = "#bottom-dev"
FAKE_NICK = "casper"

client = Client(host=HOST, port=PORT, encoding="utf-8", ssl=SSL)


# (A) a raw message handler that prints every incoming message
# FIX: add client to args, pass client into next_handler, handle bytes -> str decoding
async def print_every_message(next_handler: NextMessageHandler[Client], client: Client, message: bytes) -> None:
    print(f"{client._host}:{client._port} <<< {message.decode(client._encoding)}")
    await next_handler(client, message)


# (A) a raw message handler that prints every incoming message
# FIX: raw_handlers -> message_handlers, and we no longer need the wrapper function
client.message_handlers.insert(0, print_every_message)


# (B) periodically calls handle_raw to inject random privmsg
# FIX: no longer need to pass loop to asyncio.sleep
# FIX: two options to manually trigger raw messages:
#   1. subclass Client and implement a method that calls client._protocol.on_message(bytes)
#   2. subclass Client and provide a custom Protocol
# the first option is recommended and much easier.
async def inject_random_messages() -> None:
    try:
        while True:
            delay = 10 + random.random() * 2
            print(f"sleeping {delay} before injecting another message")
            await asyncio.sleep(delay)
            print("injecting fake message")

            msg = f":{FAKE_NICK}!user@host PRIVMSG #{NICK} :spooky ghosts!"
            assert client._protocol is not None
            client._protocol.on_message(msg.encode(client._encoding))
    except asyncio.CancelledError:
        pass


# (C) triggers blocking events
# FIX: no longer need an asyncio.Event since the caller can await client.trigger()
# to block until this (and all handlers for the event) have completed.
@client.on("my.slow.event")
async def handle_slow_event(delay: float, **kw: t.Any) -> None:
    print(f"slow event sleeping for {delay}")
    await asyncio.sleep(delay)
    print("slow event done")


# (D) triggers non-blocking custom events
# FIX: no change to client.trigger - we can ignore the returned task if we don't want to wait
@client.on("my.fast.event")
async def handle_fast_event(delay: float, **kw: t.Any) -> None:
    print(f"fast event sleeping for {delay / 4}")
    await asyncio.sleep(delay / 4)
    print("fast event done, triggering complete event")
    client.trigger("my.fast.event.done")


# (E, F) FIX OPTION 1:
#     make the function async, and use await client.send and await client.send_message
async def send_messages() -> None:
    # (E) sends well-formed rfc2812 commands
    print("sending a LIST command")
    await client.send("list", channel=CHANNEL)

    # (F) sends raw messages
    # FIX: send_raw -> await send_message
    print("sending a raw PART command")
    await client.send_message(f"PART {CHANNEL}")


#  (E, F) FIX OPTION 2:
#     keep the function async, and use create_task to schedule the client.send and client.send_message
def send_messages_fix_2() -> None:
    # (E) sends well-formed rfc2812 commands
    print("sending a LIST command")
    create_task(client.send("list", channel=CHANNEL))

    # (F) sends raw messages
    # FIX: send_raw -> send_message
    print("sending a raw PART command")
    create_task(client.send_message(f"PART {CHANNEL}"))


# (H) uses sync handlers
# FIX: same options as E, F above:
#     1. either make the function asnc so you can `await` the client.send
#  OR 2. wrap the client.send calls in create_task() to schedule them
@client.on("PING")
async def keepalive(message: str, **kwargs: t.Any) -> None:
    print(f"<<< ping {message}")
    await client.send("PONG", message=message)
    print(f">>> pong {message}")


# (I) uses async handlers
# FIX: since this example is already async, just await the client.send
@client.on("privmsg")
async def message(nick: str, target: str, message: str, **kwargs: t.Any) -> None:
    if nick == NICK:
        return
    if nick == FAKE_NICK:
        print(f"ignoring injected message from {FAKE_NICK}: {message}")
        return
    if target == NICK:
        print(f"responding directly to {nick}")
        target = nick
    else:
        print(f"responding in channel {target}")
    await client.send("privmsg", target=target, message=message)


# (J) has a poorly formed sync handler
# FIX: without changes, this raises because there's a new argument named __event__
#   two options:
#     1. add **kwargs (or **kw, etc) to the signature to capture new/unused args  (RECOMMENDED)
#     2. add __event__ as an explicit argument
#   the first option is strongly recommended, and is part of the semver contract in bottom:
#     arguments may be added to handlers in minor versions.
@client.on("join")
def join(nick: str, user: str, host: str, channel: str, **kw: t.Any) -> None:
    print(f"saw {nick} join {channel}")


# (K) races multiple waits and prints the first completed event
# FIX: use the new `wait_for` method:
from bottom import wait_for
@client.on("CLIENT_CONNECT")
async def connect(**kwargs: t.Any) -> None:
    await client.send("NICK", nick=NICK)
    await client.send("USER", user=NICK, realname="https://github.com/numberoverzero/bottom")

    first = await wait_for(client, ["RPL_ENDOFMOTD", "ERR_NOMOTD"], mode="first")
    names = [x["__event__"] for x in first]
    print(f"first complete events were {names}")

    await client.send("JOIN", channel=CHANNEL)
    print("sent join")


async def main() -> None:
    # FIX: within an async block we no longer need an explicit loop
    create_task(inject_random_messages())

    # (C) triggers blocking custom events
    # FIX: no longer need an asyncio.Event, we can directly wait on the client.trigger
    #     once all handlers have run for "my.slow.event" we'll resume in this coro
    print("triggering and waiting for my.slow.event")
    await client.trigger("my.slow.event", delay=2.5)

    # (D) triggers non-blocking custom events
    # FIX: no change, we can safely ignore the return value from client.trigger
    print("triggering and not waiting for my.fast.event")
    client.trigger("my.fast.event", delay=10)
    print("done triggering fast event")

    # (G) waits for custom events
    # FIX: return value is a dict instead of a string; either look up the name via __event__
    #    or make use of the rest of the kwargs that were passed to the event
    print("waiting for my.fast.event.done")
    ret = await client.wait("my.fast.event.done")
    print(f"event name was {ret['__event__']}")
    print("finished waiting for fast done event")

    print("connecting")
    await client.connect()

    print("waiting to see join before sending messages")
    await client.wait("join")
    print("sending some messages")
    # (E, F)
    # FIX: depends which option was used above.
    #  the first option just made the function async, so await it:
    await send_messages()
    # the second option left the function sync, so just call it:
    send_messages_fix_2()

    print("done warmup logic, waiting until disconnect occurs")
    try:
        await client.wait("client_disconnect")
    except asyncio.CancelledError:
        print("task was cancelled - manually disconnecting")
        await client.disconnect()
        print("disconnected")


if __name__ == "__main__":
    import sys
    import bottom

    print(f"python: {sys.version}")
    print(f"bottom: {bottom.__version__}")
    # FIX: don't want to use create_task here since there's no active event loop
    # luckily, asyncio.run() exists
    coro = main()
    try:
        asyncio.run(coro)
    except KeyboardInterrupt:
        print("saw ctrl+c, canceling task")
        coro.throw(asyncio.CancelledError)
