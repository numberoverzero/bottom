lightweight asyncio IRC client
==============================

bottom_ is a small no-dependency library for running simple or complex IRC clients.

It's easy to get started with built-in support for common commands, and extensible
enough to support any capabilities, including custom encryption, local events,
bridging, replication, and more.

Explicit is better than implicit: no magic importing or naming to remember for
plugins.  :ref:`Extend<Extensions>` the client with the same ``@on``
decorator.


Quickstart
----------

Create an instance:

.. code-block:: python

    import asyncio
    import bottom

    host = 'chat.freenode.net'
    port = 6697
    ssl = True

    NICK = "bottom-bot"
    CHANNEL = "#bottom-dev"

    bot = bottom.Client(host=host, port=port, ssl=ssl)


    @bot.on('CLIENT_CONNECT')
    async def connect(**kwargs):
        bot.send('NICK', nick=NICK)
        bot.send('USER', user=NICK,
                    realname='https://github.com/numberoverzero/bottom')

        # Don't try to join channels until we're past the MOTD
        await bottom.wait_for(bot, ["RPL_ENDOFMOTD", "ERR_NOMOTD"])

        bot.send('JOIN', channel=CHANNEL)


    @bot.on('PING')
    def keepalive(message: str, **kwargs):
        bot.send('PONG', message=message)


    @bot.on('PRIVMSG')
    def message(nick: str, target: str, message: str, **kwargs):
        if nick == NICK:
            return  # bot sent this message, ignore
        if target == NICK:
            target = nick  # direct message, respond directly
        # else: respond in channel
        bot.send("PRIVMSG", target=target, message=f"echo: {message}")


    async def main():
        await bot.connect()
        try:
            # serve until the connection drops...
            await bot.wait("client_disconnect")
            print("\ndisconnected by remote")
        except asyncio.CancelledError:
            # ...or we hit ctrl+c
            await bot.disconnect()
            print("\ndisconnected after ctrl+c")


    if __name__ == "__main__":
        asyncio.run(main())



Next Steps
----------

* Check out some :ref:`simple extensions<Extensions>` to add routing or
  full message encryption
* Review the list of :ref:`supported rfc2812 commands<Commands>`
* Learn :ref:`how to use events<Events>`, the core of the bottom Client,
  including how to trigger, wait on, and handle them.
* Something missing?  Want to show off a clever extension?  Contributions welcome!
  Head over to :ref:`Development<Development>` to get set up (``git pull [..] && make dev && make pr-check``)

.. toctree::
    :hidden:
    :maxdepth: 2

    user/installation
    user/api
    user/extension
    user/migration
    user/commands
    user/events
    dev/development

.. _bottom: https://github.com/numberoverzero/bottom
