import asyncio
import random

from bottom import Client

HOST = "chat.freenode.net"
PORT = 6697
SSL = True

NICK = "bottom-bot"
CHANNEL = "#bottom-dev"
FAKE_NICK = "casper"

client = Client(host=HOST, port=PORT, encoding="utf-8", ssl=SSL)


# (A) a raw message handler that prints every incoming message
def make_printer(client: Client):
    async def print_every_message(next_handler, message):
        print(f"{client.host}:{client.port} <<< {message}")
        await next_handler(message)

    return print_every_message


# (A) a raw message handler that prints every incoming message
client.raw_handlers.insert(0, make_printer(client))


# (B) periodically calls handle_raw to inject random privmsg
async def inject_random_messages():
    try:
        while True:
            delay = 10 + random.random() * 2
            print(f"sleeping {delay} before injecting another message")
            await asyncio.sleep(delay, loop=client.loop)
            print("injecting fake message")
            client.handle_raw(f":{FAKE_NICK}!user@host PRIVMSG #{NICK} :spooky ghosts!")
    except asyncio.CancelledError:
        pass


# (C) triggers blocking events
# need to use an Event for the caller to wait for this to finish
slow_event_done = asyncio.Event(loop=client.loop)


# (C) triggers blocking events
@client.on("my.slow.event")
async def handle_slow_event(delay, **kw):
    slow_event_done.clear()
    print(f"slow event sleeping for {delay}")
    await asyncio.sleep(delay, loop=client.loop)
    print("slow event done")
    slow_event_done.set()


# (D) triggers non-blocking custom events
@client.on("my.fast.event")
async def handle_fast_event(delay, **kw):
    print(f"fast event sleeping for {delay / 4}")
    await asyncio.sleep(delay / 4, loop=client.loop)
    print("fast event done, triggering complete event")
    client.trigger("my.fast.event.done")


def send_messages():
    # (E) sends well-formed rfc2812 commands
    print("sending a LIST command")
    client.send("list", channel=CHANNEL)

    # (F) sends raw messages
    print("sending a raw PART command")
    client.send_raw(f"PART {CHANNEL}")


# (H) uses sync handlers
@client.on("PING")
def keepalive(message, **kwargs):
    print(f"<<< ping {message}")
    client.send("PONG", message=message)
    print(f">>> pong {message}")


# (I) uses async handlers
@client.on("privmsg")
async def message(nick, target, message, **kwargs):
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
    client.send("privmsg", target=target, message=message)


# (J) has a poorly formed sync handler
@client.on("join")
def join(nick, user, host, channel):
    print(f"saw {nick} join {channel}")


# (K) races multiple waits and prints the first completed event
@client.on("CLIENT_CONNECT")
async def connect(**kwargs):
    client.send("NICK", nick=NICK)
    client.send("USER", user=NICK, realname="https://github.com/numberoverzero/bottom")

    # Don't try to join channels until the server has
    # sent the MOTD, or signaled that there's no MOTD.
    done, pending = await asyncio.wait(
        [client.wait("RPL_ENDOFMOTD"), client.wait("ERR_NOMOTD")],
        loop=client.loop,
        return_when=asyncio.FIRST_COMPLETED,
    )
    names = [x.result() for x in done]

    print(f"first complete events were {names}")

    # Cancel whichever waiter's event didn't come in.
    for future in pending:
        future.cancel()

    client.send("JOIN", channel=CHANNEL)
    print("sent join")


async def main():
    client.loop.create_task(inject_random_messages())

    # (C) triggers blocking custom events
    print("triggering and waiting for my.slow.event")
    client.trigger("my.slow.event", delay=2.5)
    await slow_event_done.wait()

    # (D) triggers non-blocking custom events
    print("triggering and not waiting for my.fast.event")
    client.trigger("my.fast.event", delay=10)
    print("done triggering fast event")

    # (G) waits for custom events
    print("waiting for my.fast.event.done")
    ret = await client.wait("my.fast.event.done")
    print(f"event name was {ret}")
    print("finished waiting for fast done event")

    print("connecting")
    await client.connect()

    print("waiting to see join before sending messages")
    await client.wait("join")
    print("sending some messages")
    send_messages()

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
    task = client.loop.create_task(main())
    try:
        client.loop.run_forever()
    except KeyboardInterrupt:
        print("saw ctrl+c, canceling task")
        task.cancel()
