Using Async
===========

Bottom accepts bot synchronous and async functions as callbacks.
Both of these are valid handlers for the ``privmsg`` event:

.. code-block:: python

    @client.on('privmsg')
    def synchronous_handler(**kwargs):
        print("Synchronous call")


    @client.on('privmsg')
    async def async_handler(**kwargs):
        await asyncio.sleep(1)
        print("Async call")

Connect/Disconnect
------------------

Client connect and disconnect are coroutines so that we can easily wait for
their completion before performing more actions in a handler.  However, we
don't always want to wait for the action to complete.  How can we do both?

Let's say that on disconnect we want to reconnect, then notify the room that
we're back.  We need to ``await`` for the connection before sending anything:

.. code-block:: python

    @client.on('client_disconnect')
    async def reconnect(**kwargs):
        # Wait a second so we don't flood
        await asyncio.sleep(2)

        # Wait until we've reconnected
        await client.connect()

        # Notify the room
        await client.send('privmsg', target='#bottom-dev',
                    message="I'm baaack!")

What about a handler that doesn't need an established connection to finish?
Instead of notifying the room, let's log the reconnect time and return:

.. code-block:: python

    import arrow
    import asyncio
    import logging
    logger = logging.getLogger(__name__)


    @client.on('client_disconnect')
    async def reconnect(**kwargs):
        # Wait a second so we don't flood
        await asyncio.sleep(2)

        # Schedule a connection when the loop's next available
        asyncio.create_task(client.connect())

        # Record the time of the disconnect event
        now = arrow.now()
        logger.info("Reconnect started at " + now.isoformat())

We can also wait for the ``client_connect`` event to trigger, which is slightly
different than waiting for client.connect to complete:

.. code-block:: python

    @client.on('client_disconnect')
    async def reconnect(**kwargs):
        # Wait a second so we don't flood
        await asyncio.sleep(2)

        # Schedule a connection when the loop's next available
        asyncio.create_task(client.connect())

        # Wait until client_connect has triggered
        await client.wait("client_connect")

        # Notify the room
        await client.send('privmsg', target='#bottom-dev',
                    message="I'm baaack!")

Debugging
---------

You can get more asyncio debugging info by running python with the ``-X dev`` flag:

.. code-block:: bash

    python -X dev my_bot.py

For more information, see: `Python Development Mode`_.

.. _Python Development Mode: https://docs.python.org/3/library/devmode.html#devmode
