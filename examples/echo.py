import bottom

host = 'chat.freenode.net'
port = 6697
ssl = True

NICK = "bottom-bot"
CHANNEL = "#bottom-dev"

bot = bottom.Client(host=host, port=port, ssl=ssl)


@bot.on('CLIENT_CONNECT')
def connect(**kwargs):
    bot.send('NICK', nick=NICK)
    bot.send('USER', user=NICK,
             realname='https://github.com/numberoverzero/bottom')
    bot.send('JOIN', channel=CHANNEL)


@bot.on('PING')
def keepalive(message, **kwargs):
    bot.send('PONG', message=message)


@bot.on('PRIVMSG')
def message(nick, target, message, **kwargs):
    """ Echo all messages """

    # Don't echo ourselves
    if nick == NICK:
        return
    # Respond directly to direct messages
    if target == NICK:
        bot.send("PRIVMSG", target=nick, message=message)
    # Channel message
    else:
        bot.send("PRIVMSG", target=target, message=message)

# This schedules a connection to be created when the bot's event loop
# is run.  Nothing will happen until the loop starts running to clear
# the pending coroutines.
bot.connect()

# Ctrl + C to quit
bot.loop.run_forever()
