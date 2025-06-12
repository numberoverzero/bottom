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
        await bot.send('nick', nick=NICK)
        await bot.send('user', user=NICK,
                    realname='https://github.com/numberoverzero/bottom')

        # Don't try to join channels until we're past the MOTD
        await bottom.wait_for(bot, ["RPL_ENDOFMOTD", "ERR_NOMOTD"])

        await bot.send('join', channel=CHANNEL)


    @bot.on('PING')
    async def keepalive(message: str, **kwargs):
        await bot.send('pong', message=message)


    @bot.on('PRIVMSG')
    async def message(nick: str, target: str, message: str, **kwargs):
        if nick == NICK:
            return  # bot sent this message, ignore
        if target == NICK:
            target = nick  # direct message, respond directly
        # else: respond in channel
        await bot.send("privmsg", target=target, message=f"echo: {message}")


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

* Check out some :ref:`extensions<Extensions>` that add routing or full message encryption
* Review the list of :ref:`supported rfc2812 commands<Commands>` and :ref:`supported rfc2812 responses<Events>`
* Learn how to :meth:`decorate a handler<bottom.Client.on>`, :meth:`manually trigger an event<bottom.Client.trigger>`,
  or :meth:`wait for an event<bottom.Client.wait>` in the api documentation.
* Something missing?  Contributions welcome!
  The :ref:`development<Development>` section will get you set up to ``make dev && make pr-check``

.. toctree::
    :hidden:
    :maxdepth: 2

    user/installation
    user/api
    user/extension
    user/migration
    user/commands
    dev/development

.. _bottom: https://github.com/numberoverzero/bottom
