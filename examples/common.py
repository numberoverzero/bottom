import asyncio
import bottom


host = 'chat.freenode.net'
port = 6697
ssl = True

NICK = "bottom-bot"
CHANNEL = "#bottom-dev"

client = bottom.Client(host=host, port=port, ssl=ssl)


# taken from :ref:`Patterns`
@client.on("ping")
def handle(message=None, **kwargs):
    message = message or ""
    client.send("pong", message=message)


# taken from :ref:`Patterns`
def waiter(client):
    async def wait_for(*events, return_when=asyncio.FIRST_COMPLETED):
        if not events:
            return
        done, pending = await asyncio.wait(
            [client.wait(event) for event in events],
            loop=client.loop,
            return_when=return_when)

        # Cancel any events that didn't come in.
        for future in pending:
            future.cancel()
    return wait_for


# taken from :ref:`Patterns`
wait_for = waiter(client)


@client.on("client_connect")
async def on_connect(**kwargs):
    client.send('nick', nick=NICK)
    client.send('user', user=NICK,
                realname='https://github.com/numberoverzero/bottom')

    await wait_for('rpl_endofmotd', 'err_nomotd')

    client.send('join', channel=CHANNEL)


def run():
    # This schedules a connection to be created when the bot's event loop
    # is run.  Nothing will happen until the loop starts running to clear
    # the pending coroutines.
    client.loop.create_task(client.connect())

    # Ctrl + C to quit
    print(
        "Connecting to {} on port {} as {} in channel {}".format(
            host, port, NICK, CHANNEL))
    client.loop.run_forever()
